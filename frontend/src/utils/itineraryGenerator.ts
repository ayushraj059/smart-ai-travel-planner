import { TripParams, GeneratedItinerary, DayItinerary, Activity, BudgetType } from '../types';

const activityTemplates: Record<string, Array<{ time: string; name: string; desc: string }>> = {
  Beaches: [
    { time: '07:30 AM', name: 'Sunrise beach walk', desc: 'Catch the stunning sunrise along the golden shoreline' },
    { time: '10:00 AM', name: 'Snorkeling adventure', desc: 'Explore colorful coral reefs and marine life beneath the waves' },
    { time: '01:00 PM', name: 'Beach volleyball', desc: 'Join locals for an energetic game on the warm sand' },
    { time: '03:30 PM', name: 'Parasailing experience', desc: 'Soar above the ocean for breathtaking aerial views' },
    { time: '06:00 PM', name: 'Sunset beach bonfire', desc: 'Relax by the fire as the golden sun dips below the horizon' },
  ],
  Nightlife: [
    { time: '07:00 PM', name: 'Rooftop cocktail bar', desc: 'Sip handcrafted cocktails with panoramic city views' },
    { time: '09:00 PM', name: 'Live music venue', desc: 'Experience local bands and a vibrant music scene' },
    { time: '10:30 PM', name: 'Night market exploration', desc: 'Browse vibrant stalls with street food and local artisan goods' },
    { time: '11:30 PM', name: 'Night club experience', desc: 'Dance to the beats at one of the city\'s hottest clubs' },
  ],
  Culture: [
    { time: '09:00 AM', name: 'Visit local museums', desc: 'Explore art, history, and cultural exhibitions' },
    { time: '11:00 AM', name: 'Historical walking tour', desc: 'Walk through the old town and learn about local heritage' },
    { time: '02:00 PM', name: 'Traditional craft workshop', desc: 'Learn traditional crafts from skilled local artisans' },
    { time: '04:00 PM', name: 'Local art gallery', desc: 'Admire works by regional and contemporary artists' },
    { time: '05:30 PM', name: 'Heritage temple visit', desc: 'Explore ancient temples and sacred spiritual landmarks' },
  ],
  Adventure: [
    { time: '07:00 AM', name: 'Morning hiking trail', desc: 'Trek through scenic mountain or forest paths at dawn' },
    { time: '10:00 AM', name: 'Rock climbing session', desc: 'Challenge yourself on natural rock faces with a certified guide' },
    { time: '01:00 PM', name: 'White-water rafting', desc: 'Navigate thrilling rapids with an experienced rafting crew' },
    { time: '04:00 PM', name: 'Zip-lining through the jungle', desc: 'Soar through lush treetops on an exhilarating zip-line' },
    { time: '06:00 PM', name: 'Kayaking at sunset', desc: 'Paddle through scenic waterways as the sun dips below the hills' },
  ],
  Zoo: [
    { time: '09:00 AM', name: 'Wildlife sanctuary visit', desc: 'Get up close with exotic animals in their natural habitat' },
    { time: '11:30 AM', name: 'Aquarium exploration', desc: 'Discover fascinating marine creatures from around the world' },
    { time: '02:00 PM', name: 'Bird sanctuary walk', desc: 'Spot rare and colorful birds in their natural environment' },
    { time: '04:00 PM', name: 'Safari experience', desc: 'Observe majestic wildlife in an authentic open-air setting' },
  ],
  Shopping: [
    { time: '10:00 AM', name: 'Local artisan market', desc: 'Browse handcrafted goods, textiles, spices, and local arts' },
    { time: '01:00 PM', name: 'Main shopping boulevard', desc: 'Explore flagship stores and boutiques on the high street' },
    { time: '04:00 PM', name: 'Souvenir & antique hunt', desc: 'Find unique mementos and vintage treasures to take home' },
    { time: '06:00 PM', name: 'Designer district stroll', desc: 'Window-shop luxury brands in the upscale quarter of the city' },
  ],
  Nature: [
    { time: '07:00 AM', name: 'Botanical garden visit', desc: 'Wander through lush gardens showcasing exotic flora and fauna' },
    { time: '10:00 AM', name: 'National park day trip', desc: 'Explore protected natural landscapes, trails, and viewpoints' },
    { time: '01:00 PM', name: 'Waterfall hike', desc: 'Trek through dense forest to reach a stunning hidden waterfall' },
    { time: '04:00 PM', name: 'Scenic valley viewpoint', desc: 'Take in sweeping panoramic views from a dramatic lookout' },
  ],
  Wellness: [
    { time: '07:00 AM', name: 'Sunrise yoga session', desc: 'Start the day with a calming yoga practice in the open air' },
    { time: '10:00 AM', name: 'Traditional spa treatment', desc: 'Indulge in local massage techniques and holistic therapies' },
    { time: '02:00 PM', name: 'Meditation & mindfulness class', desc: 'Reconnect with inner peace guided by a local wellness expert' },
    { time: '05:00 PM', name: 'Hot spring soak', desc: 'Unwind in natural thermal hot springs surrounded by nature' },
  ],
  Photography: [
    { time: '06:30 AM', name: 'Golden hour photography', desc: 'Capture stunning landscapes in the magical early morning light' },
    { time: '10:00 AM', name: 'Street photography tour', desc: 'Document the vibrant daily life in the local neighborhoods' },
    { time: '03:00 PM', name: 'Iconic landmarks shoot', desc: 'Photograph the most famous and photogenic spots in the city' },
    { time: '06:00 PM', name: 'Sunset skyline shots', desc: 'Frame the breathtaking city skyline bathed in golden light' },
  ],
};

const foodTemplates: Record<string, Array<{ time: string; name: string; desc: string }>> = {
  Vegetarian: [
    { time: '08:00 AM', name: 'Vegetarian breakfast café', desc: 'Fresh plant-based breakfast to fuel the day ahead' },
    { time: '12:30 PM', name: 'Garden vegetarian bistro', desc: 'Seasonal vegetarian dishes with farm-fresh ingredients' },
    { time: '07:00 PM', name: 'Vegan fine dining restaurant', desc: 'Creative plant-based cuisine in an elegant setting' },
  ],
  'Non-Vegetarian': [
    { time: '08:00 AM', name: 'Local breakfast diner', desc: 'Hearty local breakfast with eggs, cured meats, and fresh bread' },
    { time: '12:30 PM', name: 'Traditional local restaurant', desc: 'Authentic local cuisine featuring signature meat dishes' },
    { time: '07:00 PM', name: 'BBQ & grill experience', desc: 'Perfectly grilled local meats in a lively and festive atmosphere' },
  ],
  Halal: [
    { time: '08:00 AM', name: 'Halal-certified café', desc: 'Certified halal breakfast at a welcoming and cozy café' },
    { time: '12:30 PM', name: 'Halal cuisine restaurant', desc: 'Authentic halal dishes prepared with bold local flavors' },
    { time: '07:00 PM', name: 'Halal fine dining', desc: 'Upscale halal-certified dining with impeccable service' },
  ],
  Vegan: [
    { time: '08:00 AM', name: 'Raw vegan breakfast bar', desc: 'Nutrient-packed raw vegan options to energize your morning' },
    { time: '12:30 PM', name: 'Vegan bistro', desc: 'Colorful and inventive vegan lunch with seasonal ingredients' },
    { time: '07:00 PM', name: 'Vegan tasting menu', desc: 'Elaborate plant-based tasting menu crafted by a renowned chef' },
  ],
  'No Preference': [
    { time: '08:00 AM', name: 'Local breakfast spot', desc: 'Try the most-loved local morning favorites with the residents' },
    { time: '12:30 PM', name: 'Street food tour', desc: 'Sample a vibrant array of local street food delicacies' },
    { time: '07:00 PM', name: 'Signature restaurant', desc: 'Dinner at one of the city\'s most celebrated dining destinations' },
  ],
};

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function toMinutes(time: string): number {
  const [hm, period] = time.split(' ');
  const [h, m] = hm.split(':').map(Number);
  let hours = h;
  if (period === 'PM' && h !== 12) hours += 12;
  if (period === 'AM' && h === 12) hours = 0;
  return hours * 60 + m;
}

export function generateItinerary(params: TripParams): GeneratedItinerary {
  const start = parseLocalDate(params.startDate);
  const end = parseLocalDate(params.endDate);
  const numDays = Math.max(1, Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1);

  const selectedActivities = params.activities.length > 0 ? params.activities : ['Culture'];
  const foodPref = params.foodPreferences.length > 0 ? params.foodPreferences[0] : 'No Preference';
  const foodPool = foodTemplates[foodPref] || foodTemplates['No Preference'];

  const toActivity = (t: { time: string; name: string; desc: string }, category: string): Activity => ({
    time: t.time,
    name: t.name,
    description: t.desc,
    category,
    cost: 0,
    currency: '',
    duration_hours: 1,
  });

  const schedule: DayItinerary[] = [];

  for (let i = 0; i < numDays; i++) {
    const dayDate = new Date(start);
    dayDate.setDate(start.getDate() + i);
    const activities: Activity[] = [];

    if (i === 0) {
      activities.push({
        time: '12:00 PM',
        name: `Arrive in ${params.destination}`,
        description: 'Transfer to your accommodation, check in, and freshen up',
        category: 'Travel',
        cost: 0, currency: '', duration_hours: 1,
      });
      const cat = selectedActivities[0];
      const picks = shuffle(activityTemplates[cat] || activityTemplates['Culture']).slice(0, 2);
      picks.forEach(p => activities.push(toActivity(p, cat)));
      activities.push(toActivity({ ...foodPool[2], time: '07:00 PM' }, 'Food & Dining'));
    } else if (i === numDays - 1 && numDays > 1) {
      activities.push(toActivity(foodPool[0], 'Food & Dining'));
      const cat = selectedActivities[(i) % selectedActivities.length];
      const pick = shuffle(activityTemplates[cat] || activityTemplates['Culture'])[0];
      activities.push(toActivity({ ...pick, time: '10:00 AM' }, cat));
      activities.push({
        time: '02:00 PM',
        name: `Depart from ${params.destination}`,
        description: 'Transfer to the airport and head home with wonderful memories',
        category: 'Travel',
        cost: 0, currency: '', duration_hours: 1,
      });
    } else {
      const cat = selectedActivities[(i - 1) % selectedActivities.length];
      const picks = shuffle(activityTemplates[cat] || activityTemplates['Culture']).slice(0, 3);

      activities.push(toActivity(foodPool[0], 'Food & Dining'));
      activities.push(toActivity({ ...picks[0], time: '09:00 AM' }, cat));
      activities.push(toActivity(foodPool[1], 'Food & Dining'));
      if (picks[1]) activities.push(toActivity({ ...picks[1], time: '02:30 PM' }, cat));
      if (picks[2]) activities.push(toActivity({ ...picks[2], time: '04:30 PM' }, cat));
      activities.push(toActivity(foodPool[2], 'Food & Dining'));
    }

    activities.sort((a, b) => toMinutes(a.time) - toMinutes(b.time));

    const dayTitle =
      i === 0
        ? `Arrival in ${params.destination}`
        : i === numDays - 1 && numDays > 1
          ? `Departure Day`
          : `Exploring ${params.destination}`;

    schedule.push({ day: i + 1, dateStr: formatDate(dayDate), title: dayTitle, activities, dailyCost: 0 });
  }

  const budgetLabel: Record<BudgetType, string> = {
    Budget: 'Budget',
    Moderate: 'Moderate',
    Luxury: 'Luxury',
  };

  return {
    id: Date.now().toString(),
    destination: params.destination,
    startDate: formatDate(start),
    endDate: formatDate(end),
    numDays,
    travelers: params.travelers,
    budget: budgetLabel[params.budget] as BudgetType,
    tags: selectedActivities,
    schedule,
    hotels: [],
    totalCostPerPerson: 0,
    currency: '',
    budgetStatus: '',
  };
}
