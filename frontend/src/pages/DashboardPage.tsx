import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/layout/Sidebar';
import { Plane, Shield, Fingerprint, Compass, User, Search, Cloud } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import { GeneratedItinerary } from '../types';
import { weatherApi, WeatherDay, localDateStr } from '../services/api';

function WeatherWidget() {
  const [inputCity, setInputCity] = useState('');
  const [searchedCity, setSearchedCity] = useState('');
  const [weather, setWeather] = useState<WeatherDay[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Default to most recently planned trip city
  useEffect(() => {
    const trips: GeneratedItinerary[] = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
    if (trips.length > 0) {
      const city = trips[trips.length - 1].destination;
      setInputCity(city);
      setSearchedCity(city);
    }
  }, []);

  useEffect(() => {
    if (!searchedCity) { setWeather([]); setError(''); return; }
    let cancelled = false;
    setLoading(true);
    setError('');
    weatherApi.getWeather(searchedCity, localDateStr(0), localDateStr(5))
      .then(days => {
        if (cancelled) return;
        if (days.length === 0) setError(`No forecast found for "${searchedCity}"`);
        else setWeather(days);
      })
      .catch(() => { if (!cancelled) setError('Could not fetch weather. Check city name.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [searchedCity]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const city = inputCity.trim();
    if (city) setSearchedCity(city);
  };

  const today = weather[0];
  const forecast = weather.slice(1);

  const dayName = (dateStr: string) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short' });
  };

  return (
    <div className="bg-navy-600 border border-navy-400 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Cloud size={15} className="text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-300">Weather</h2>
        </div>
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputCity}
            onChange={e => setInputCity(e.target.value)}
            placeholder="Search city…"
            className="bg-navy-700 border border-navy-500 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 w-36 transition-all"
          />
          <button
            type="submit"
            className="p-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors"
          >
            <Search size={12} className="text-white" />
          </button>
        </form>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-500 text-xs py-4">
          <div className="w-3 h-3 border border-slate-500 border-t-transparent rounded-full animate-spin" />
          Fetching forecast for {searchedCity}…
        </div>
      )}

      {error && !loading && (
        <p className="text-slate-500 text-xs py-4">{error}</p>
      )}

      {!loading && !error && weather.length === 0 && (
        <p className="text-slate-600 text-xs py-4 text-center">
          Search a city to see the weather forecast.
        </p>
      )}

      {!loading && today && (
        <div>
          {/* Today — prominent */}
          <div className="flex items-center justify-between mb-4 bg-navy-700 border border-navy-500 rounded-xl px-4 py-3">
            <div>
              <p className="text-slate-400 text-xs mb-0.5">Today · {searchedCity}</p>
              <p className="text-white font-bold text-3xl leading-none">{today.tempMax}°C</p>
              <p className="text-slate-400 text-xs mt-1">{today.description} · Low {today.tempMin}°C</p>
            </div>
            <span className="text-5xl">{today.icon}</span>
          </div>

          {/* Forecast strip */}
          {forecast.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Upcoming days</p>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {forecast.map(w => (
                  <div
                    key={w.date}
                    className="flex-shrink-0 bg-navy-700 border border-navy-500 rounded-xl px-3 py-2.5 text-center min-w-[68px]"
                  >
                    <p className="text-xs text-slate-400 font-medium mb-1">{dayName(w.date)}</p>
                    <p className="text-2xl leading-none mb-1">{w.icon}</p>
                    <p className="text-white text-xs font-semibold">{w.tempMax}°</p>
                    <p className="text-slate-500 text-xs">{w.tempMin}°</p>
                    <p className="text-slate-600 text-xs mt-1 leading-tight">{w.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tripCount, setTripCount] = useState(0);

  useEffect(() => {
    const trips: GeneratedItinerary[] = JSON.parse(localStorage.getItem('voyonata_trips') || '[]');
    setTripCount(trips.length);
  }, []);

  const statCards = [
    {
      icon: Plane,
      iconBg: 'bg-indigo-500/20',
      iconColor: 'text-indigo-400',
      value: String(tripCount),
      label: 'Trips Planned',
    },
    {
      icon: Shield,
      iconBg: 'bg-emerald-500/20',
      iconColor: 'text-emerald-400',
      value: 'Active',
      label: 'Security Status',
    },
    {
      icon: Fingerprint,
      iconBg: 'bg-violet-500/20',
      iconColor: 'text-violet-400',
      value: '—',
      label: 'Passkeys Registered',
    },
  ];

  const actionCards = [
    {
      icon: Compass,
      iconBg: 'bg-orange-500/20',
      iconColor: 'text-orange-400',
      title: 'Plan a Trip',
      desc: 'Generate your perfect itinerary',
      to: '/plan',
    },
    {
      icon: User,
      iconBg: 'bg-emerald-500/20',
      iconColor: 'text-emerald-400',
      title: 'Edit Profile',
      desc: 'Update your name and email',
      to: '/profile',
    },
  ];

  return (
    <div className="flex min-h-screen bg-navy-900">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-3xl">
          {/* Welcome */}
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-white mb-1">
              Welcome back,{' '}
              <span className="text-indigo-400">{user?.name}</span>
            </h1>
            <p className="text-slate-400 text-sm">
              Your secure travel command center. Plan your next adventure below.
            </p>
          </div>

          {/* Stat Cards */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {statCards.map(({ icon: Icon, iconBg, iconColor, value, label }) => (
              <div key={label} className="bg-navy-600 border border-navy-400 rounded-xl p-5">
                <div className={`w-9 h-9 ${iconBg} rounded-lg flex items-center justify-center mb-4`}>
                  <Icon size={17} className={iconColor} />
                </div>
                <p className="text-2xl font-bold text-white leading-none mb-1">{value}</p>
                <p className="text-xs text-slate-400">{label}</p>
              </div>
            ))}
          </div>

          {/* Weather Widget */}
          <div className="mb-8">
            <WeatherWidget />
          </div>

          {/* Quick Actions */}
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Quick Actions
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {actionCards.map(({ icon: Icon, iconBg, iconColor, title, desc, to }) => (
              <button
                key={title}
                onClick={() => navigate(to)}
                className="bg-navy-600 border border-navy-400 rounded-xl p-5 text-left hover:border-indigo-500/40 hover:bg-navy-500 transition-all group"
              >
                <div className={`w-9 h-9 ${iconBg} rounded-lg flex items-center justify-center mb-4`}>
                  <Icon size={17} className={iconColor} />
                </div>
                <p className="font-medium text-white text-sm group-hover:text-indigo-300 transition-colors">
                  {title}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
