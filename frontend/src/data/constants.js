export const STATIONS = [
  { id: 0, name: "Botanical Garden", code: "BG", lines: ["Magenta Line", "Blue Line"], hub: true },
  { id: 1, name: "Dwarka Sec 21", code: "DW21", lines: ["Blue Line", "Airport Express"], hub: true },
  { id: 2, name: "Hauz Khas", code: "HK", lines: ["Yellow Line", "Magenta Line"], hub: true },
  { id: 3, name: "Kashmere Gate", code: "KG", lines: ["Red Line", "Yellow Line", "Violet Line"], hub: true },
  { id: 4, name: "Rajiv Chowk", code: "RC", lines: ["Blue Line", "Yellow Line"], hub: true }
];

export const LINES = [
  { id: 0, name: "Blue Line", color: "#0284c7", border: "border-sky-500", text: "text-sky-400", bg: "bg-sky-500/10", badge: "bg-sky-500/20 text-sky-300 border-sky-500/30" },
  { id: 1, name: "Magenta Line", color: "#db2777", border: "border-pink-500", text: "text-pink-400", bg: "bg-pink-500/10", badge: "bg-pink-500/20 text-pink-300 border-pink-500/30" },
  { id: 2, name: "Red Line", color: "#ef4444", border: "border-red-500", text: "text-red-400", bg: "bg-red-500/10", badge: "bg-red-500/20 text-red-300 border-red-500/30" },
  { id: 3, name: "Yellow Line", color: "#eab308", border: "border-yellow-500", text: "text-yellow-400", bg: "bg-yellow-500/10", badge: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30" }
];

export const DAYS_OF_WEEK = [
  { id: 1, name: "Monday", short: "Mon" },
  { id: 5, name: "Tuesday", short: "Tue" },
  { id: 6, name: "Wednesday", short: "Wed" },
  { id: 4, name: "Thursday", short: "Thu" },
  { id: 0, name: "Friday", short: "Fri" },
  { id: 2, name: "Saturday", short: "Sat" },
  { id: 3, name: "Sunday", short: "Sun" }
];

export const CAPACITIES = [
  { value: 1500, label: "4-Coach (1,500 pax)", desc: "Standard feeder rake" },
  { value: 1800, label: "6-Coach (1,800 pax)", desc: "Standard mainline rake" },
  { value: 2400, label: "8-Coach (2,400 pax)", desc: "High-capacity heavy metro" }
];

export const PRESETS = [
  {
    title: "Rajiv Chowk Evening Rush",
    desc: "Peak transit interchange with extreme passenger congestion",
    hour: 18,
    day_of_week: 1,
    from_station: 4, // Rajiv Chowk
    to_station: 2,   // Hauz Khas
    line_color: 3,   // Yellow Line
    train_capacity: 2400,
    expected_tier: "SEVERE_RUSH",
    icon: "AlertOctagon",
    badgeColor: "bg-red-500/20 text-red-400 border-red-500/30"
  },
  {
    title: "Kashmere Gate Morning Peak",
    desc: "Heavy morning influx from Northern suburban corridors",
    hour: 9,
    day_of_week: 1,
    from_station: 3, // Kashmere Gate
    to_station: 4,   // Rajiv Chowk
    line_color: 3,   // Yellow Line
    train_capacity: 2400,
    expected_tier: "SEVERE_RUSH",
    icon: "TrendingUp",
    badgeColor: "bg-red-500/20 text-red-400 border-red-500/30"
  },
  {
    title: "Botanical Garden Midday",
    desc: "Balanced afternoon interchange flow with moderate demand",
    hour: 14,
    day_of_week: 6,
    from_station: 0, // Botanical Garden
    to_station: 1,   // Dwarka Sec 21
    line_color: 1,   // Magenta Line
    train_capacity: 1800,
    expected_tier: "MODERATE_TRAFFIC",
    icon: "Clock",
    badgeColor: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
  },
  {
    title: "Dwarka Sec 21 Late Night",
    desc: "Off-peak low density terminal service to conserve fleet",
    hour: 22,
    day_of_week: 0,
    from_station: 1, // Dwarka Sec 21
    to_station: 0,   // Botanical Garden
    line_color: 0,   // Blue Line
    train_capacity: 1500,
    expected_tier: "OFF_PEAK",
    icon: "Moon",
    badgeColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
  }
];

export const THRESHOLDS = {
  CRITICAL: 1500,
  MODERATE: 800
};
