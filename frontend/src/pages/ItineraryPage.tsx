import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import { GeneratedItinerary, Activity, HotelRecommendation } from '../types';
import { itineraryApi } from '../services/api';
import {
  ArrowLeft, Trash2, MapPin, Calendar, Users, Wallet,
  Clock, Utensils, Hotel, TrendingUp, TrendingDown, Minus, X, Pencil, Plus,
} from 'lucide-react';

const categoryColors: Record<string, string> = {
  attraction: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
  restaurant:  'bg-rose-500/15 text-rose-300 border-rose-500/25',
  Culture:     'bg-amber-500/15 text-amber-300 border-amber-500/25',
  Beaches:     'bg-cyan-500/15 text-cyan-300 border-cyan-500/25',
  Nightlife:   'bg-violet-500/15 text-violet-300 border-violet-500/25',
  Adventure:   'bg-orange-500/15 text-orange-300 border-orange-500/25',
  Shopping:    'bg-pink-500/15 text-pink-300 border-pink-500/25',
  Nature:      'bg-green-500/15 text-green-300 border-green-500/25',
};

function fmt(n: number) {
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function BudgetBadge({ status }: { status: string }) {
  if (!status) return null;
  const lower = status.toLowerCase();
  if (lower.includes('over'))
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/15 text-red-300 border border-red-500/25">
        <TrendingUp size={10} /> Over budget
      </span>
    );
  if (lower.includes('under'))
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
        <TrendingDown size={10} /> Under budget
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
      <Minus size={10} /> Within budget
    </span>
  );
}

// ── Activity form ──────────────────────────────────────────────────────────────

interface ActivityFormData {
  time: string;
  duration_hours: number;
  category: string;
  name: string;
  description: string;
  cost: number;
  currency: string;
}

function ActivityForm({
  initial,
  tripCurrency,
  onSave,
  onCancel,
  submitLabel,
}: {
  initial?: Partial<ActivityFormData>;
  tripCurrency: string;
  onSave: (data: ActivityFormData) => void;
  onCancel: () => void;
  submitLabel: string;
}) {
  const [form, setForm] = useState<ActivityFormData>({
    time: '',
    duration_hours: 1,
    category: 'attraction',
    name: '',
    description: '',
    cost: 0,
    currency: tripCurrency,
    ...initial,
  });

  const set = <K extends keyof ActivityFormData>(k: K, v: ActivityFormData[K]) =>
    setForm(f => ({ ...f, [k]: v }));

  return (
    <div className="bg-navy-700 border border-indigo-500/30 rounded-xl p-4 mt-3 space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Time</label>
          <input
            type="time"
            value={form.time}
            onChange={e => set('time', e.target.value)}
            className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Duration (hrs)</label>
          <input
            type="number"
            min={0.5}
            step={0.5}
            value={form.duration_hours}
            onChange={e => set('duration_hours', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Category</label>
          <select
            value={form.category}
            onChange={e => set('category', e.target.value)}
            className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="attraction">Attraction</option>
            <option value="restaurant">Restaurant</option>
          </select>
        </div>
      </div>

      <div>
        <label className="text-xs text-slate-500 mb-1 block">Place Name</label>
        <input
          type="text"
          value={form.name}
          onChange={e => set('name', e.target.value)}
          placeholder="e.g. Colaba Causeway"
          className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600"
        />
      </div>

      <div>
        <label className="text-xs text-slate-500 mb-1 block">Notes</label>
        <input
          type="text"
          value={form.description}
          onChange={e => set('description', e.target.value)}
          placeholder="Shop for souvenirs and explore the street market"
          className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Cost per person</label>
          <input
            type="number"
            min={0}
            step={10}
            value={form.cost}
            onChange={e => set('cost', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Currency</label>
          <input
            type="text"
            value={form.currency}
            onChange={e => set('currency', e.target.value.toUpperCase())}
            placeholder="INR"
            className="w-full px-3 py-2 bg-navy-600 border border-navy-400 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600"
          />
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 pt-1">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={() => onSave(form)}
          disabled={!form.name.trim() || !form.time}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-medium rounded-lg transition-colors"
        >
          {submitLabel}
        </button>
      </div>
    </div>
  );
}

// ── Activity row ───────────────────────────────────────────────────────────────

function ActivityRow({
  activity, isLast, tripCurrency, onRemove, onEdit,
}: {
  activity: Activity;
  isLast: boolean;
  tripCurrency: string;
  onRemove?: () => void;
  onEdit?: () => void;
}) {
  const isFood = activity.category === 'restaurant' || activity.category === 'Food & Dining';
  const colorClass = categoryColors[activity.category] || 'bg-slate-500/15 text-slate-300 border-slate-500/25';
  const cur = activity.currency || tripCurrency;
  const hasCost = (activity.cost ?? 0) > 0;

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 z-10 ${isFood ? 'bg-rose-400' : 'bg-indigo-500'}`} />
        {!isLast && <div className="w-px flex-1 bg-navy-400 mt-1" />}
      </div>
      <div className={`flex-1 min-w-0 ${isLast ? 'pb-2' : 'pb-6'}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <span className="text-xs text-slate-500 flex items-center gap-1 mb-1">
              {isFood ? <Utensils size={10} /> : <Clock size={10} />}
              {activity.time}
              {(activity.duration_hours ?? 0) > 0 && (
                <span className="ml-1">· {activity.duration_hours}h</span>
              )}
            </span>
            <p className="text-white font-medium text-sm leading-snug">{activity.name}</p>
            {isFood && (activity.cuisine || activity.rating != null) && (
              <div className="flex items-center gap-2 mt-0.5">
                {activity.cuisine && (
                  <span className="text-xs text-rose-300/80">{activity.cuisine}</span>
                )}
                {activity.rating != null && (
                  <span className="text-xs text-amber-400">★ {activity.rating.toFixed(1)}</span>
                )}
              </div>
            )}
            <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">{activity.description}</p>
            {isFood && activity.famous_dishes && activity.famous_dishes.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {activity.famous_dishes.map(dish => (
                  <span key={dish} className="px-2 py-0.5 bg-rose-500/10 text-rose-300/80 border border-rose-500/20 rounded-full text-xs">
                    {dish}
                  </span>
                ))}
              </div>
            )}
            {hasCost && (
              <p className="text-slate-500 text-xs mt-1">{cur} {fmt(activity.cost)}/person</p>
            )}
            {!hasCost && <p className="text-emerald-600 text-xs mt-1">Free</p>}
          </div>
          <div className="flex items-start gap-1 shrink-0 mt-1">
            <span className={`px-2 py-0.5 rounded-full text-xs border ${colorClass}`}>
              {activity.category}
            </span>
            {onEdit && (
              <button
                onClick={onEdit}
                className="p-0.5 text-slate-600 hover:text-indigo-400 transition-colors"
                title="Edit activity"
              >
                <Pencil size={11} />
              </button>
            )}
            {onRemove && (
              <button
                onClick={onRemove}
                className="p-0.5 text-slate-600 hover:text-red-400 transition-colors"
                title="Remove from plan"
              >
                <X size={12} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Hotel card ─────────────────────────────────────────────────────────────────

function HotelCard({ hotel, budget }: { hotel: HotelRecommendation; budget: string }) {
  const budgetColor = budget === 'Budget'
    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25'
    : budget === 'Luxury'
    ? 'bg-amber-500/15 text-amber-300 border-amber-500/25'
    : 'bg-indigo-500/15 text-indigo-300 border-indigo-500/25';

  return (
    <div className="bg-navy-600 border border-navy-400 rounded-xl p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-white font-medium text-sm">{hotel.name}</h3>
            <span className={`px-2 py-0.5 rounded-full text-xs border ${budgetColor}`}>{budget}</span>
          </div>
          {hotel.stars != null && hotel.stars > 0 && (
            <p className="text-amber-400 text-xs mt-0.5">{'★'.repeat(hotel.stars)}{'☆'.repeat(5 - hotel.stars)}</p>
          )}
          <p className="text-slate-400 text-xs mt-2 leading-relaxed">{hotel.notes}</p>
        </div>
        {(hotel.costPerNight ?? 0) > 0 && (
          <div className="text-right shrink-0">
            <p className="text-white text-sm font-medium">{hotel.currency} {fmt(hotel.costPerNight)}</p>
            <p className="text-slate-500 text-xs">per person/night</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function ItineraryPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<GeneratedItinerary | null>(null);
  const [activeTab, setActiveTab] = useState<number | 'hotels'>(0);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editing, setEditing] = useState<[number, number] | null>(null);
  const [addingToDayIdx, setAddingToDayIdx] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDeleteDay, setConfirmDeleteDay] = useState(false);

  useEffect(() => {
    const trips: GeneratedItinerary[] = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
    const found = trips.find(t => t.id === id);
    if (found) setTrip(found);
    else navigate('/trips');
  }, [id, navigate]);

  // Close open forms when switching tabs
  useEffect(() => {
    setEditing(null);
    setAddingToDayIdx(null);
    setConfirmDeleteDay(false);
  }, [activeTab]);

  const persistItinerary = async (updated: GeneratedItinerary) => {
    setTrip(updated);
    const trips: GeneratedItinerary[] = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
    localStorage.setItem('voyonata_trips', JSON.stringify(trips.map(t => t.id === updated.id ? updated : t)));
    const token = localStorage.getItem('voyonata_token');
    if (token) {
      setSaving(true);
      try {
        await itineraryApi.update(token, updated.id, updated);
      } catch { /* silent — localStorage is the source of truth */ }
      finally { setSaving(false); }
    }
  };

  const handleDelete = () => {
    const trips: GeneratedItinerary[] = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
    localStorage.setItem('voyonata_trips', JSON.stringify(trips.filter(t => t.id !== id)));
    const token = localStorage.getItem('voyonata_token');
    if (token && id) {
      itineraryApi.delete(token, id).catch(() => {});
    }
    navigate('/trips');
  };

  const handleRemoveActivity = async (dayIdx: number, actIdx: number) => {
    if (!trip) return;
    await persistItinerary({
      ...trip,
      schedule: trip.schedule.map((day, dIdx) =>
        dIdx !== dayIdx ? day : { ...day, activities: day.activities.filter((_, aIdx) => aIdx !== actIdx) }
      ),
    });
  };

  const handleAddActivity = async (dayIdx: number, formData: ActivityFormData) => {
    if (!trip) return;
    const newActivity: Activity = {
      time: formData.time,
      name: formData.name,
      description: formData.description,
      category: formData.category,
      cost: formData.cost,
      currency: formData.currency || trip.currency,
      duration_hours: formData.duration_hours,
    };
    setAddingToDayIdx(null);
    await persistItinerary({
      ...trip,
      schedule: trip.schedule.map((day, dIdx) =>
        dIdx !== dayIdx ? day : { ...day, activities: [...day.activities, newActivity] }
      ),
    });
  };

  const handleDeleteDay = async (dIdx: number) => {
    if (!trip) return;
    const newSchedule = trip.schedule.filter((_, i) => i !== dIdx);
    const updated: GeneratedItinerary = { ...trip, schedule: newSchedule, numDays: newSchedule.length };
    setConfirmDeleteDay(false);
    // If we deleted the last tab, move back one
    if (typeof activeTab === 'number' && activeTab >= newSchedule.length) {
      setActiveTab(newSchedule.length > 0 ? newSchedule.length - 1 : 'hotels');
    }
    await persistItinerary(updated);
  };

  const handleEditActivity = async (dayIdx: number, actIdx: number, formData: ActivityFormData) => {
    if (!trip) return;
    setEditing(null);
    await persistItinerary({
      ...trip,
      schedule: trip.schedule.map((day, dIdx) =>
        dIdx !== dayIdx ? day : {
          ...day,
          activities: day.activities.map((a, aIdx) =>
            aIdx !== actIdx ? a : {
              ...a,
              time: formData.time,
              name: formData.name,
              description: formData.description,
              category: formData.category,
              cost: formData.cost,
              currency: formData.currency || trip.currency,
              duration_hours: formData.duration_hours,
            }
          ),
        }
      ),
    });
  };

  if (!trip) {
    return (
      <div className="flex min-h-screen bg-navy-900">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </main>
      </div>
    );
  }

  const hotels = trip.hotels ?? [];
  const currentDay = activeTab !== 'hotels' ? trip.schedule[activeTab as number] : null;
  const dayIdx = activeTab as number;

  return (
    <div className="flex min-h-screen bg-navy-900">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-8 py-8">

          {/* Top bar */}
          <div className="flex items-center justify-between mb-7">
            <button
              onClick={() => navigate('/trips')}
              className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 text-sm transition-colors"
            >
              <ArrowLeft size={15} />
              Back to Trips
            </button>
            <div className="flex items-center gap-3">
              {saving && (
                <span className="flex items-center gap-1.5 text-slate-500 text-xs">
                  <div className="w-3 h-3 border border-slate-500 border-t-transparent rounded-full animate-spin" />
                  Saving…
                </span>
              )}
              {showDeleteConfirm ? (
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-xs">Delete this trip?</span>
                  <button onClick={handleDelete} className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-medium rounded-lg transition-colors">
                    Yes, Delete
                  </button>
                  <button onClick={() => setShowDeleteConfirm(false)} className="px-3 py-1.5 bg-navy-500 hover:bg-navy-400 text-slate-300 text-xs font-medium rounded-lg transition-colors">
                    Cancel
                  </button>
                </div>
              ) : (
                <button onClick={() => setShowDeleteConfirm(true)} className="flex items-center gap-1.5 text-slate-500 hover:text-red-400 text-sm transition-colors">
                  <Trash2 size={14} />
                  Delete Trip
                </button>
              )}
            </div>
          </div>

          {/* Destination + meta */}
          <div className="mb-5">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full shrink-0 mt-1" />
                <h1 className="text-2xl font-bold text-white">{trip.destination}</h1>
              </div>
              <BudgetBadge status={trip.budgetStatus ?? ''} />
            </div>

            <div className="flex flex-wrap items-center gap-4 text-slate-400 text-xs mb-4">
              <span className="flex items-center gap-1.5"><Calendar size={12} />{trip.startDate} – {trip.endDate}</span>
              <span className="flex items-center gap-1.5"><MapPin size={12} />{trip.numDays} day{trip.numDays !== 1 ? 's' : ''}</span>
              <span className="flex items-center gap-1.5"><Users size={12} />{trip.travelers} traveler{trip.travelers > 1 ? 's' : ''}</span>
              <span className="flex items-center gap-1.5"><Wallet size={12} />{trip.budget}</span>
            </div>

            {(trip.totalCostPerPerson ?? 0) > 0 && (
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-navy-700 border border-navy-500 rounded-xl px-4 py-3">
                  <p className="text-slate-500 text-xs mb-1">Per Person</p>
                  <p className="text-white font-semibold text-sm">{trip.currency} {fmt(trip.totalCostPerPerson)}</p>
                  <p className="text-slate-600 text-xs mt-0.5">{trip.numDays} days total</p>
                </div>
                <div className="bg-navy-700 border border-navy-500 rounded-xl px-4 py-3">
                  <p className="text-slate-500 text-xs mb-1">Grand Total</p>
                  <p className="text-indigo-300 font-semibold text-sm">{trip.currency} {fmt(trip.totalCostPerPerson * trip.travelers)}</p>
                  <p className="text-slate-600 text-xs mt-0.5">for {trip.travelers} traveler{trip.travelers > 1 ? 's' : ''}</p>
                </div>
                <div className="bg-navy-700 border border-navy-500 rounded-xl px-4 py-3">
                  <p className="text-slate-500 text-xs mb-1">Per Day/Person</p>
                  <p className="text-white font-semibold text-sm">{trip.currency} {fmt(trip.totalCostPerPerson / trip.numDays)}</p>
                  <p className="text-slate-600 text-xs mt-0.5">avg daily spend</p>
                </div>
              </div>
            )}

            {trip.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {trip.tags.map((tag, i) => (
                  <span
                    key={tag}
                    className={`px-3 py-1 rounded-full text-xs border font-medium ${
                      ['bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
                       'bg-violet-500/20 text-violet-300 border-violet-500/30',
                       'bg-blue-500/20 text-blue-300 border-blue-500/30',
                       'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
                       'bg-amber-500/20 text-amber-300 border-amber-500/30'][i % 5]
                    }`}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Destination overview */}
          {trip.destinationOverview && (
            <div className="mb-6 bg-navy-600 border border-navy-400 rounded-xl p-5 space-y-3.5">
              <h3 className="text-sm font-semibold text-slate-200">About {trip.destination}</h3>

              {trip.destinationOverview.weather_summary && (
                <div className="flex gap-3">
                  <span className="text-base leading-none shrink-0 mt-0.5">🌤️</span>
                  <p className="text-slate-400 text-xs leading-relaxed">{trip.destinationOverview.weather_summary}</p>
                </div>
              )}

              {trip.destinationOverview.must_visit_places.length > 0 && (
                <div className="flex gap-3 items-start">
                  <MapPin size={13} className="text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-slate-500 mb-1.5">Must Visit</p>
                    <div className="flex flex-wrap gap-1.5">
                      {trip.destinationOverview.must_visit_places.map(place => (
                        <span key={place} className="px-2.5 py-0.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-full text-xs">
                          {place}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {trip.destinationOverview.local_dishes.length > 0 && (
                <div className="flex gap-3 items-start">
                  <Utensils size={13} className="text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-slate-500 mb-1.5">Local Dishes</p>
                    <div className="flex flex-wrap gap-1.5">
                      {trip.destinationOverview.local_dishes.map(dish => (
                        <span key={dish} className="px-2.5 py-0.5 bg-rose-500/10 text-rose-300 border border-rose-500/20 rounded-full text-xs">
                          {dish}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {trip.destinationOverview.culture_insight && (
                <div className="flex gap-3">
                  <span className="text-base leading-none shrink-0 mt-0.5">🎭</span>
                  <p className="text-slate-400 text-xs leading-relaxed">{trip.destinationOverview.culture_insight}</p>
                </div>
              )}
            </div>
          )}

          {/* Tabs */}
          <div className="flex gap-0 overflow-x-auto border-b border-navy-400 mb-6">
            {trip.schedule.map((day, idx) => (
              <button
                key={day.day}
                onClick={() => setActiveTab(idx)}
                className={`px-4 py-2.5 text-left whitespace-nowrap transition-all border-b-2 -mb-px ${
                  activeTab === idx
                    ? 'text-indigo-400 border-indigo-500 bg-indigo-600/10'
                    : 'text-slate-500 border-transparent hover:text-slate-300 hover:bg-navy-600'
                }`}
              >
                <p className="text-sm font-medium">Day {day.day}</p>
                {day.weather && (
                  <p className="text-xs text-slate-500 mt-0.5">
                    {day.weather.icon} {day.weather.tempMax}°/{day.weather.tempMin}°
                  </p>
                )}
              </button>
            ))}
            <button
              onClick={() => setActiveTab('hotels')}
              className={`px-4 py-2.5 flex items-center gap-1.5 whitespace-nowrap transition-all border-b-2 -mb-px text-sm font-medium ${
                activeTab === 'hotels'
                  ? 'text-indigo-400 border-indigo-500 bg-indigo-600/10'
                  : 'text-slate-500 border-transparent hover:text-slate-300 hover:bg-navy-600'
              }`}
            >
              <Hotel size={13} />
              Hotels
            </button>
          </div>

          {/* Day view */}
          {currentDay && (
            <div>
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-white font-semibold">{currentDay.title}</h2>
                  <p className="text-slate-500 text-xs mt-0.5">{currentDay.dateStr}</p>
                  {confirmDeleteDay ? (
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-slate-400 text-xs">Delete Day {currentDay.day}?</span>
                      <button
                        onClick={() => handleDeleteDay(dayIdx)}
                        className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white text-xs font-medium rounded-lg transition-colors"
                      >
                        Yes, Delete
                      </button>
                      <button
                        onClick={() => setConfirmDeleteDay(false)}
                        className="px-2.5 py-1 bg-navy-500 hover:bg-navy-400 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirmDeleteDay(true)}
                      className="flex items-center gap-1 mt-1.5 text-slate-600 hover:text-red-400 text-xs transition-colors"
                    >
                      <Trash2 size={11} />
                      Delete day
                    </button>
                  )}
                </div>
                <div className="text-right space-y-1">
                  {currentDay.weather && (
                    <p className="text-sm text-slate-300">
                      {currentDay.weather.icon} {currentDay.weather.description}
                      <span className="text-slate-500 ml-1.5">
                        {currentDay.weather.tempMax}° / {currentDay.weather.tempMin}°C
                      </span>
                    </p>
                  )}
                  {(currentDay.dailyCost ?? 0) > 0 && (
                    <p className="text-xs text-slate-500">
                      {trip.currency} {fmt(currentDay.dailyCost)}/person today
                    </p>
                  )}
                </div>
              </div>

              {/* Activity list */}
              <div>
                {currentDay.activities.map((activity, idx) => {
                  const isEditing =
                    editing !== null && editing[0] === dayIdx && editing[1] === idx;
                  const isLastVisible =
                    idx === currentDay.activities.length - 1 && addingToDayIdx !== dayIdx;

                  return (
                    <div key={idx}>
                      {isEditing ? (
                        <div className="pl-6">
                          <ActivityForm
                            initial={{
                              time: activity.time,
                              duration_hours: activity.duration_hours,
                              category: activity.category,
                              name: activity.name,
                              description: activity.description,
                              cost: activity.cost,
                              currency: activity.currency || trip.currency,
                            }}
                            tripCurrency={trip.currency ?? ''}
                            onSave={formData => handleEditActivity(dayIdx, idx, formData)}
                            onCancel={() => setEditing(null)}
                            submitLabel="Update Activity"
                          />
                        </div>
                      ) : (
                        <ActivityRow
                          activity={activity}
                          isLast={isLastVisible}
                          tripCurrency={trip.currency ?? ''}
                          onRemove={() => handleRemoveActivity(dayIdx, idx)}
                          onEdit={() => {
                            setAddingToDayIdx(null);
                            setEditing([dayIdx, idx]);
                          }}
                        />
                      )}
                    </div>
                  );
                })}

                {currentDay.activities.length === 0 && addingToDayIdx !== dayIdx && (
                  <p className="text-slate-500 text-sm mb-4">No activities scheduled for this day.</p>
                )}
              </div>

              {/* Add activity */}
              {addingToDayIdx === dayIdx ? (
                <ActivityForm
                  tripCurrency={trip.currency ?? ''}
                  onSave={formData => handleAddActivity(dayIdx, formData)}
                  onCancel={() => setAddingToDayIdx(null)}
                  submitLabel="Add Activity"
                />
              ) : (
                <button
                  onClick={() => { setEditing(null); setAddingToDayIdx(dayIdx); }}
                  className="mt-5 flex items-center gap-2 text-xs text-slate-500 hover:text-indigo-400 border border-dashed border-navy-400 hover:border-indigo-500/40 rounded-lg px-4 py-2.5 w-full justify-center transition-all"
                >
                  <Plus size={13} />
                  Add Activity
                </button>
              )}
            </div>
          )}

          {/* Hotels view */}
          {activeTab === 'hotels' && (
            <div>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-white font-semibold">Recommended Hotels</h2>
                <span className="text-slate-500 text-xs">{trip.budget} tier</span>
              </div>
              {hotels.length > 0 ? (
                <div className="space-y-4">
                  {hotels.map((hotel, i) => (
                    <HotelCard key={i} hotel={hotel} budget={trip.budget} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Hotel size={32} className="text-navy-400 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">No hotel recommendations in this itinerary.</p>
                  <p className="text-slate-600 text-xs mt-1">Re-generate to get hotel suggestions.</p>
                </div>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
