const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:8001';
const RAG_URL = import.meta.env.VITE_RAG_URL || 'http://localhost:8002';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (HTTP ${res.status})`);
  }
  return res.json() as Promise<T>;
}

function json(method: string, body: unknown, token?: string): RequestInit {
  return {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  };
}

// ── Auth Service ──────────────────────────────────────────────────────────────

export interface MeResponse {
  email: string;
  full_name: string;
  created_at: string;
}

export const authApi = {
  signup: (email: string, password: string, full_name: string) =>
    request<{ access_token: string }>(`${AUTH_URL}/signup`, json('POST', { email, password, full_name })),

  login: (email: string, password: string) =>
    request<{ access_token: string }>(`${AUTH_URL}/login`, json('POST', { email, password })),

  me: (token: string) =>
    request<MeResponse>(`${AUTH_URL}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// ── RAG Service ───────────────────────────────────────────────────────────────

export interface WeatherForecastDay {
  date: string;
  description: string;
  icon: string;
  temp_max: number;
  temp_min: number;
}

export interface ItineraryRequest {
  city: string;
  start_date: string;
  end_date: string;
  num_travelers: number;
  budget_preference: string;
  activity_preferences: string[];
  food_preferences: string[];
  weather_forecast?: WeatherForecastDay[];
}

export function localDateStr(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export interface ItineraryActivity {
  time: string;
  place_name: string;
  category: string;
  duration_hours: number;
  notes: string;
  estimated_cost_per_person: number;
  currency: string;
  cuisine?: string;
  rating?: number;
  famous_dishes?: string[];
}

export interface ItineraryDay {
  day: number;
  date: string;
  theme: string;
  activities: ItineraryActivity[];
  daily_cost_per_person: number;
}

export interface HotelResponse {
  name: string;
  notes: string;
  estimated_cost_per_person_per_night: number;
  currency: string;
  stars?: number;
}

export interface DestinationOverview {
  weather_summary: string;
  must_visit_places: string[];
  local_dishes: string[];
  culture_insight: string;
}

export interface ItineraryResponse {
  city: string;
  start_date: string;
  end_date: string;
  num_days: number;
  num_travelers: number;
  budget_preference: string;
  days: ItineraryDay[];
  recommended_hotels: HotelResponse[];
  summary: {
    total_estimated_cost_per_person: number;
    total_estimated_cost: number;
    currency: string;
    budget_status: string;
    highlights: string[];
  };
  destination_overview?: DestinationOverview;
}

export const ragApi = {
  generateItinerary: (req: ItineraryRequest, token?: string) =>
    request<ItineraryResponse>(`${RAG_URL}/itinerary`, json('POST', req, token)),
};

// ── Itinerary persistence (auth-service) ──────────────────────────────────────

export const itineraryApi = {
  save: (token: string, id: string, data: unknown) =>
    request<{ itinerary_id: string }>(`${AUTH_URL}/itineraries`, json('POST', { itinerary_id: id, data }, token)),

  update: (token: string, id: string, data: unknown) =>
    request<{ message: string }>(`${AUTH_URL}/itineraries/${encodeURIComponent(id)}`, json('PUT', { itinerary_id: id, data }, token)),

  delete: (token: string, id: string) =>
    request<{ message: string }>(`${AUTH_URL}/itineraries/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    }),

  list: (token: string) =>
    request<{ itinerary_id: string; destination: string; start_date: string; end_date: string; num_days: number; saved_at: string }[]>(
      `${AUTH_URL}/itineraries`,
      { headers: { Authorization: `Bearer ${token}` } },
    ),
};

// ── Weather (Open-Meteo, free, no key required) ───────────────────────────────

export interface WeatherDay {
  date: string;
  icon: string;
  description: string;
  tempMax: number;
  tempMin: number;
}

function wmoToInfo(code: number): { icon: string; description: string } {
  if (code === 0)  return { icon: '☀️', description: 'Clear' };
  if (code <= 2)   return { icon: '🌤️', description: 'Partly Cloudy' };
  if (code === 3)  return { icon: '☁️', description: 'Overcast' };
  if (code <= 48)  return { icon: '🌫️', description: 'Foggy' };
  if (code <= 67)  return { icon: '🌧️', description: 'Rainy' };
  if (code <= 77)  return { icon: '❄️', description: 'Snowy' };
  if (code <= 82)  return { icon: '🌦️', description: 'Showers' };
  return { icon: '⛈️', description: 'Stormy' };
}

export const weatherApi = {
  async getWeather(city: string, startDate: string, endDate: string): Promise<WeatherDay[]> {
    const geoRes = await fetch(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`
    );
    const geo = await geoRes.json();
    if (!geo.results?.length) return [];

    const { latitude, longitude } = geo.results[0];
    const weatherRes = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
      `&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto` +
      `&start_date=${startDate}&end_date=${endDate}`
    );
    const data = await weatherRes.json();
    if (!data.daily) return [];

    return (data.daily.time as string[]).map((date, i) => ({
      date,
      ...wmoToInfo(data.daily.weathercode[i] as number),
      tempMax: Math.round(data.daily.temperature_2m_max[i] as number),
      tempMin: Math.round(data.daily.temperature_2m_min[i] as number),
    }));
  },
};
