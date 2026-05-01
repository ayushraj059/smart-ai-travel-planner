export interface User {
  name: string;
  email: string;
}

export type BudgetType = 'Budget' | 'Moderate' | 'Luxury';

export interface TripParams {
  destination: string;
  startDate: string;
  endDate: string;
  travelers: number;
  budget: BudgetType;
  activities: string[];
  foodPreferences: string[];
}

export interface DestinationOverview {
  weather_summary: string;
  must_visit_places: string[];
  local_dishes: string[];
  culture_insight: string;
}

export interface WeatherInfo {
  icon: string;
  description: string;
  tempMax: number;
  tempMin: number;
}

export interface Activity {
  time: string;
  name: string;
  description: string;
  category: string;
  cost: number;
  currency: string;
  duration_hours: number;
  cuisine?: string;
  rating?: number;
  famous_dishes?: string[];
}

export interface HotelRecommendation {
  name: string;
  notes: string;
  costPerNight: number;
  currency: string;
  stars?: number;
}

export interface DayItinerary {
  day: number;
  dateStr: string;
  title: string;
  activities: Activity[];
  dailyCost: number;
  weather?: WeatherInfo;
}

export interface GeneratedItinerary {
  id: string;
  destination: string;
  startDate: string;
  endDate: string;
  numDays: number;
  travelers: number;
  budget: BudgetType;
  tags: string[];
  schedule: DayItinerary[];
  hotels: HotelRecommendation[];
  totalCostPerPerson: number;
  currency: string;
  budgetStatus: string;
  destinationOverview?: DestinationOverview;
}
