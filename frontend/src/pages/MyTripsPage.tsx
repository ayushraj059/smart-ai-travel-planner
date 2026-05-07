import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import { GeneratedItinerary } from '../types';
import { MapPin, Calendar, Users, Compass } from 'lucide-react';

export default function MyTripsPage() {
  const [trips, setTrips] = useState<GeneratedItinerary[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const stored: GeneratedItinerary[] = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
    setTrips(stored.reverse());
  }, []);

  return (
    <div className="flex min-h-screen bg-navy-900">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-3xl">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-white mb-1">My Trips</h1>
            <p className="text-slate-400 text-sm">All your planned adventures in one place.</p>
          </div>

          {trips.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 bg-navy-600 rounded-2xl flex items-center justify-center mb-5">
                <Compass size={28} className="text-slate-500" />
              </div>
              <p className="text-slate-300 font-medium mb-1">No trips yet</p>
              <p className="text-slate-500 text-sm mb-6">
                Start by planning your first adventure
              </p>
              <button
                onClick={() => navigate('/plan')}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-colors"
              >
                Plan a Trip →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {trips.map(trip => (
                <button
                  key={trip.id}
                  onClick={() => navigate(`/itinerary/${trip.id}`)}
                  className="bg-navy-600 border border-navy-400 rounded-xl p-5 text-left hover:border-indigo-500/40 hover:bg-navy-500 transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 bg-emerald-400 rounded-full" />
                        <h3 className="text-white font-semibold text-base group-hover:text-indigo-300 transition-colors">
                          {trip.destination}
                        </h3>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-slate-400 text-xs mb-3">
                        <span className="flex items-center gap-1.5">
                          <Calendar size={12} />
                          {trip.startDate} – {trip.endDate}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <MapPin size={12} />
                          {trip.numDays} days
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Users size={12} />
                          {trip.travelers} traveler{trip.travelers > 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {trip.tags.map(tag => (
                          <span
                            key={tag}
                            className="px-2.5 py-0.5 bg-navy-500 border border-navy-300 rounded-full text-xs text-slate-300"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-medium px-2.5 py-1 bg-indigo-600/20 text-indigo-300 rounded-lg border border-indigo-500/20 block mb-1.5">
                        {trip.budget}
                      </span>
                      {(trip.totalCostPerPerson ?? 0) > 0 && (
                        <p className="text-xs text-slate-400 text-right">
                          {trip.currency} {trip.totalCostPerPerson.toLocaleString(undefined, { maximumFractionDigits: 0 })}<span className="text-slate-600">/person</span>
                        </p>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
