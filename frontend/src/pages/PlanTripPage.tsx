import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import { ragApi, weatherApi, itineraryApi, WeatherDay } from '../services/api';
import { TripParams, BudgetType, GeneratedItinerary, WeatherInfo } from '../types';
import {
  MapPin,
  Calendar,
  Users,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Wallet,
  Cloud,
} from 'lucide-react';

const ACTIVITY_OPTIONS = [
  'Beaches', 'Nightlife', 'Culture', 'Adventure',
  'Zoo', 'Shopping', 'Nature', 'Wellness', 'Photography',
];

const FOOD_OPTIONS = [
  'Vegetarian', 'Non-Vegetarian', 'Vegan', 'Halal', 'No Preference',
];

const BUDGET_OPTIONS: { value: BudgetType; label: string; desc: string; icon: string }[] = [
  { value: 'Budget', label: 'Budget', desc: 'Hostels, street food, public transport', icon: '💰' },
  { value: 'Moderate', label: 'Moderate', desc: 'Mid-range hotels, local restaurants', icon: '💰💰' },
  { value: 'Luxury', label: 'Luxury', desc: 'Premium hotels, fine dining experiences', icon: '💰💰💰' },
];

const defaultParams: TripParams = {
  destination: '',
  startDate: '',
  endDate: '',
  travelers: 1,
  budget: 'Moderate',
  activities: [],
  foodPreferences: [],
};

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-0 mb-10">
      {[1, 2, 3].map((step, idx) => (
        <div key={step} className="flex items-center">
          <div
            className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
              current >= step ? 'bg-indigo-500' : 'bg-navy-400'
            }`}
          />
          {idx < 2 && (
            <div className="w-28 h-px mx-1" style={{
              background: current > step + 1
                ? '#6366f1'
                : 'repeating-linear-gradient(90deg,#1e2d4a 0,#1e2d4a 5px,transparent 5px,transparent 10px)',
            }} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function PlanTripPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [params, setParams] = useState<TripParams>(defaultParams);
  const [generating, setGenerating] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState('');
  const [previewWeather, setPreviewWeather] = useState<WeatherDay[]>([]);
  const [weatherLoading, setWeatherLoading] = useState(false);

  useEffect(() => {
    if (!params.destination.trim() || !params.startDate || !params.endDate) {
      setPreviewWeather([]);
      return;
    }
    let cancelled = false;
    setWeatherLoading(true);
    weatherApi.getWeather(params.destination, params.startDate, params.endDate)
      .then(days => { if (!cancelled) setPreviewWeather(days); })
      .catch(() => { if (!cancelled) setPreviewWeather([]); })
      .finally(() => { if (!cancelled) setWeatherLoading(false); });
    return () => { cancelled = true; };
  }, [params.destination, params.startDate, params.endDate]);

  const toggleActivity = (a: string) => {
    setParams(p => ({
      ...p,
      activities: p.activities.includes(a)
        ? p.activities.filter(x => x !== a)
        : [...p.activities, a],
    }));
  };

  const toggleFood = (f: string) => {
    setParams(p => ({
      ...p,
      foodPreferences: p.foodPreferences.includes(f)
        ? p.foodPreferences.filter(x => x !== f)
        : [...p.foodPreferences, f],
    }));
  };

  const validateStep1 = () => {
    const e: Record<string, string> = {};
    if (!params.destination.trim()) e.destination = 'Please enter a destination.';
    if (!params.startDate) e.startDate = 'Please select a start date.';
    if (!params.endDate) e.endDate = 'Please select an end date.';
    if (params.startDate && params.endDate && params.startDate > params.endDate)
      e.endDate = 'End date must be after start date.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const validateStep2 = () => {
    const e: Record<string, string> = {};
    if (params.activities.length === 0) e.activities = 'Please select at least one activity.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const goNext = () => {
    if (step === 1 && validateStep1()) setStep(2);
    else if (step === 2 && validateStep2()) setStep(3);
  };

  const handleGenerate = async () => {
    setApiError('');
    setGenerating(true);
    try {
      // Reuse already-fetched preview weather; re-fetch only if somehow empty
      const weatherDays: WeatherDay[] = previewWeather.length > 0
        ? previewWeather
        : await weatherApi.getWeather(params.destination, params.startDate, params.endDate).catch(() => []);

      const ragResponse = await ragApi.generateItinerary({
        city: params.destination.toLowerCase(),
        start_date: params.startDate,
        end_date: params.endDate,
        num_travelers: params.travelers,
        budget_preference: params.budget,
        activity_preferences: params.activities,
        food_preferences: params.foodPreferences.length > 0 ? params.foodPreferences : ['No Preference'],
        weather_forecast: weatherDays.map(w => ({
          date: w.date,
          description: w.description,
          icon: w.icon,
          temp_max: w.tempMax,
          temp_min: w.tempMin,
        })),
      });

      const weatherMap: Record<string, WeatherInfo> = {};
      for (const w of weatherDays) {
        const { date, ...info } = w;
        weatherMap[date] = info;
      }

      const itinerary: GeneratedItinerary = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        destination: params.destination,
        startDate: ragResponse.start_date,
        endDate: ragResponse.end_date,
        numDays: ragResponse.num_days,
        travelers: ragResponse.num_travelers,
        budget: ragResponse.budget_preference as BudgetType,
        tags: ragResponse.summary.highlights,
        totalCostPerPerson: ragResponse.summary.total_estimated_cost_per_person,
        currency: ragResponse.summary.currency,
        budgetStatus: ragResponse.summary.budget_status,
        schedule: ragResponse.days.map(d => ({
          day: d.day,
          dateStr: d.date,
          title: d.theme,
          dailyCost: d.daily_cost_per_person,
          weather: weatherMap[d.date],
          activities: d.activities.map(a => ({
            time: a.time,
            name: a.place_name,
            description: a.notes,
            category: a.category,
            cost: a.estimated_cost_per_person,
            currency: a.currency,
            duration_hours: a.duration_hours,
            cuisine: a.cuisine,
            rating: a.rating,
            famous_dishes: a.famous_dishes ?? [],
          })),
        })),
        hotels: (ragResponse.recommended_hotels || []).map(h => ({
          name: h.name,
          notes: h.notes,
          costPerNight: h.estimated_cost_per_person_per_night,
          currency: h.currency,
          stars: h.stars,
        })),
        destinationOverview: ragResponse.destination_overview,
      };

      const trips = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
      trips.push(itinerary);
      localStorage.setItem('voyonata_trips', JSON.stringify(trips));
      const token = localStorage.getItem('voyonata_token');
      if (token) {
        itineraryApi.save(token, itinerary.id, itinerary).catch(() => {});
      }
      navigate(`/itinerary/${itinerary.id}`);
    } catch (err) {
      setApiError((err as Error).message);
      setGenerating(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-navy-900">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-8 py-10">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Sparkles size={18} className="text-indigo-400" />
              <h1 className="text-2xl font-semibold text-white">Plan Your Trip</h1>
            </div>
            <p className="text-slate-400 text-sm">
              Tell us about your dream trip and we'll craft the perfect itinerary.
            </p>
          </div>

          <StepIndicator current={step} />

          {/* ── Step 1: Basic Info ── */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Where do you want to go?
                </label>
                <div className="relative">
                  <MapPin
                    size={15}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
                  />
                  <input
                    type="text"
                    value={params.destination}
                    onChange={e => setParams(p => ({ ...p, destination: e.target.value }))}
                    placeholder="e.g. Tokyo, Paris, Bali…"
                    className="w-full pl-10 pr-4 py-3 bg-navy-600 border border-navy-400 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
                  />
                </div>
                {errors.destination && (
                  <p className="text-red-400 text-xs mt-1.5">{errors.destination}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <span className="flex items-center gap-1.5">
                      <Calendar size={13} /> Start Date
                    </span>
                  </label>
                  <input
                    type="date"
                    value={params.startDate}
                    onChange={e => setParams(p => ({ ...p, startDate: e.target.value }))}
                    className="w-full px-4 py-3 bg-navy-600 border border-navy-400 rounded-xl text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
                  />
                  {errors.startDate && (
                    <p className="text-red-400 text-xs mt-1.5">{errors.startDate}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <span className="flex items-center gap-1.5">
                      <Calendar size={13} /> End Date
                    </span>
                  </label>
                  <input
                    type="date"
                    value={params.endDate}
                    onChange={e => setParams(p => ({ ...p, endDate: e.target.value }))}
                    min={params.startDate}
                    className="w-full px-4 py-3 bg-navy-600 border border-navy-400 rounded-xl text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
                  />
                  {errors.endDate && (
                    <p className="text-red-400 text-xs mt-1.5">{errors.endDate}</p>
                  )}
                </div>
              </div>

              {/* Weather forecast preview — shown as soon as destination + dates are filled */}
              {(weatherLoading || previewWeather.length > 0) && (
                <div>
                  <p className="text-xs text-slate-500 mb-2 flex items-center gap-1.5">
                    <Cloud size={11} /> Weather forecast for your trip
                  </p>
                  {weatherLoading ? (
                    <div className="flex items-center gap-2 text-slate-500 text-xs">
                      <div className="w-3 h-3 border border-slate-500 border-t-transparent rounded-full animate-spin" />
                      Fetching forecast…
                    </div>
                  ) : (
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {previewWeather.map(w => (
                        <div
                          key={w.date}
                          className="flex-shrink-0 bg-navy-700 border border-navy-500 rounded-xl px-3 py-2.5 text-center min-w-[72px]"
                        >
                          <p className="text-xs text-slate-500 mb-1">{w.date.slice(5)}</p>
                          <p className="text-xl leading-none mb-1">{w.icon}</p>
                          <p className="text-white text-xs font-semibold">{w.tempMax}°</p>
                          <p className="text-slate-500 text-xs">{w.tempMin}°</p>
                          <p className="text-slate-500 text-xs mt-1 leading-tight truncate max-w-[60px]">{w.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  <span className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Users size={13} /> Number of Travelers
                    </span>
                    <span className="text-indigo-400 font-semibold">{params.travelers}</span>
                  </span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={params.travelers}
                  onChange={e => setParams(p => ({ ...p, travelers: Number(e.target.value) }))}
                  className="w-full h-1.5 bg-navy-400 rounded-full appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-slate-600 mt-1">
                  <span>1</span>
                  <span>20</span>
                </div>
              </div>
            </div>
          )}

          {/* ── Step 2: Preferences ── */}
          {step === 2 && (
            <div className="space-y-7">
              {/* Budget */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  <span className="flex items-center gap-1.5">
                    <Wallet size={13} /> Budget Preference
                  </span>
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {BUDGET_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setParams(p => ({ ...p, budget: opt.value }))}
                      className={`p-4 rounded-xl border text-left transition-all ${
                        params.budget === opt.value
                          ? 'border-indigo-500 bg-indigo-600/10'
                          : 'border-navy-400 bg-navy-600 hover:border-navy-300'
                      }`}
                    >
                      <span className="text-lg block mb-1">{opt.icon}</span>
                      <p className="text-white text-sm font-medium">{opt.label}</p>
                      <p className="text-slate-500 text-xs mt-0.5 leading-tight">{opt.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Activities */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Activity Preferences
                </label>
                <p className="text-xs text-slate-500 mb-3">Select all that interest you</p>
                <div className="flex flex-wrap gap-2">
                  {ACTIVITY_OPTIONS.map(a => (
                    <button
                      key={a}
                      onClick={() => toggleActivity(a)}
                      className={`px-3.5 py-2 rounded-full text-sm border transition-all ${
                        params.activities.includes(a)
                          ? 'border-indigo-500 bg-indigo-600/20 text-indigo-300'
                          : 'border-navy-400 bg-navy-600 text-slate-400 hover:border-navy-300 hover:text-slate-200'
                      }`}
                    >
                      {a}
                    </button>
                  ))}
                </div>
                {errors.activities && (
                  <p className="text-red-400 text-xs mt-2">{errors.activities}</p>
                )}
              </div>

              {/* Food */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Food Preferences
                </label>
                <p className="text-xs text-slate-500 mb-3">Select all that apply</p>
                <div className="flex flex-wrap gap-2">
                  {FOOD_OPTIONS.map(f => (
                    <button
                      key={f}
                      onClick={() => toggleFood(f)}
                      className={`px-3.5 py-2 rounded-full text-sm border transition-all ${
                        params.foodPreferences.includes(f)
                          ? 'border-emerald-500 bg-emerald-600/20 text-emerald-300'
                          : 'border-navy-400 bg-navy-600 text-slate-400 hover:border-navy-300 hover:text-slate-200'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── Step 3: Review & Generate ── */}
          {step === 3 && !generating && (
            <div className="space-y-5">
              <div className="bg-navy-600 border border-navy-400 rounded-xl p-6 space-y-4">
                <h3 className="text-white font-semibold">Trip Summary</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-500 text-xs mb-0.5">Destination</p>
                    <p className="text-white font-medium">{params.destination}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs mb-0.5">Budget</p>
                    <p className="text-white font-medium">{params.budget}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs mb-0.5">Dates</p>
                    <p className="text-white font-medium">
                      {params.startDate} → {params.endDate}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs mb-0.5">Travelers</p>
                    <p className="text-white font-medium">
                      {params.travelers} person{params.travelers > 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-slate-500 text-xs mb-1.5">Activities</p>
                  <div className="flex flex-wrap gap-1.5">
                    {params.activities.map(a => (
                      <span key={a} className="px-2.5 py-0.5 bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 rounded-full text-xs">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
                {params.foodPreferences.length > 0 && (
                  <div>
                    <p className="text-slate-500 text-xs mb-1.5">Food Preferences</p>
                    <div className="flex flex-wrap gap-1.5">
                      {params.foodPreferences.map(f => (
                        <span key={f} className="px-2.5 py-0.5 bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 rounded-full text-xs">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={handleGenerate}
                className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <Sparkles size={16} />
                Generate My Itinerary
              </button>
            </div>
          )}

          {/* ── API error ── */}
          {apiError && !generating && (
            <div className="mb-4 flex items-start gap-2.5 p-3.5 bg-red-500/10 border border-red-500/25 rounded-xl text-red-400 text-sm">
              <span className="shrink-0 mt-0.5">⚠</span>
              <span>{apiError}</span>
            </div>
          )}

          {/* ── Generating loader ── */}
          {generating && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-6" />
              <p className="text-white font-semibold text-lg mb-2">Crafting your itinerary…</p>
              <p className="text-slate-400 text-sm">
                Our AI is planning the perfect trip to{' '}
                <span className="text-indigo-400">{params.destination}</span>
              </p>
            </div>
          )}

          {/* Navigation buttons */}
          {!generating && (
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-navy-400">
              <button
                onClick={() => setStep(s => Math.max(1, s - 1))}
                disabled={step === 1}
                className="flex items-center gap-1.5 px-4 py-2.5 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={16} />
                Back
              </button>

              {step < 3 ? (
                <button
                  onClick={goNext}
                  className="flex items-center gap-1.5 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-colors"
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              ) : null}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
