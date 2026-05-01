import logging
from datetime import datetime, timedelta

from .models import ItineraryResponse, ItineraryDay, ItineraryActivity

log = logging.getLogger(__name__)

# Rough daily budget caps per person (in USD equivalent — used for status labelling only)
_BUDGET_CAPS_USD = {
    "Budget": 50.0,
    "Moderate": 150.0,
    "Luxury": float("inf"),
}

# Approx USD conversion multipliers for common currencies (rough guidance only)
_TO_USD = {
    "INR": 0.012,
    "USD": 1.0,
    "EUR": 1.08,
    "THB": 0.028,
    "SGD": 0.74,
    "AED": 0.27,
    "KRW": 0.00073,
    "JPY": 0.0067,
}


def validate_and_fix(itinerary: ItineraryResponse, plan: dict) -> ItineraryResponse:
    """
    Post-processing validation layer:
    1. Sort each day's activities by time
    2. Detect and resolve time overlaps (push later activities forward)
    3. Recalculate daily_cost_per_person from actual activity costs
    4. Recalculate summary totals and budget_status
    """
    fixed_days = [_fix_day(day) for day in itinerary.days]

    total_per_person = sum(d.daily_cost_per_person for d in fixed_days)
    total_all = total_per_person * itinerary.num_travelers

    currency = itinerary.summary.currency or _infer_currency(fixed_days)
    budget_status = _budget_status(
        total_per_person,
        currency,
        itinerary.num_days,
        plan.get("budget_preference", "Moderate"),
    )

    log.info(
        f"Validation complete — total/person={total_per_person:.2f} {currency}, "
        f"status={budget_status}"
    )

    return itinerary.model_copy(update={
        "days": fixed_days,
        "summary": itinerary.summary.model_copy(update={
            "total_estimated_cost_per_person": round(total_per_person, 2),
            "total_estimated_cost": round(total_all, 2),
            "currency": currency,
            "budget_status": budget_status,
        }),
    })


def _fix_day(day: ItineraryDay) -> ItineraryDay:
    activities = sorted(day.activities, key=lambda a: _parse_time(a.time))
    activities = _resolve_overlaps(activities)
    daily_cost = round(sum(a.estimated_cost_per_person for a in activities), 2)
    return day.model_copy(update={"activities": activities, "daily_cost_per_person": daily_cost})


def _resolve_overlaps(activities: list[ItineraryActivity]) -> list[ItineraryActivity]:
    """Push the start time of any activity that overlaps the previous one."""
    if not activities:
        return activities

    fixed = [activities[0]]
    for act in activities[1:]:
        prev = fixed[-1]
        prev_end = _add_hours(_parse_time(prev.time), prev.duration_hours)
        current_start = _parse_time(act.time)
        if current_start < prev_end:
            # Push forward by 15-minute grace gap
            new_start = prev_end + timedelta(minutes=15)
            act = act.model_copy(update={"time": new_start.strftime("%H:%M")})
            log.debug(f"Shifted '{act.place_name}' to {act.time} to resolve overlap")
        fixed.append(act)
    return fixed


def _parse_time(t: str) -> datetime:
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(t.strip(), fmt)
        except ValueError:
            continue
    return datetime.strptime("09:00", "%H:%M")


def _add_hours(dt: datetime, hours: float) -> datetime:
    return dt + timedelta(hours=hours)


def _infer_currency(days: list[ItineraryDay]) -> str:
    for day in days:
        for act in day.activities:
            if act.currency:
                return act.currency
    return "USD"


def _budget_status(total_per_person: float, currency: str, num_days: int, budget_pref: str) -> str:
    daily_per_person = total_per_person / max(num_days, 1)
    rate = _TO_USD.get(currency.upper(), 1.0)
    daily_usd = daily_per_person * rate
    cap = _BUDGET_CAPS_USD.get(budget_pref, 150.0)

    if daily_usd <= cap * 0.8:
        return "under budget"
    if daily_usd <= cap:
        return "within budget"
    return "over budget"
