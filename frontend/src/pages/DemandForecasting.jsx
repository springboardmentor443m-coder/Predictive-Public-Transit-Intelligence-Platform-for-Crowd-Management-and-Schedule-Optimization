import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Clock,
  MapPin,
  Download,
  AlertTriangle,
  Building,
  Calendar,
  Send,
  Search,
  Filter,
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../api/client';

export default function DemandForecasting({ onDispatchAlert, onNavigate }) {
  const [selectedHorizon, setSelectedHorizon] = useState('Next 1 Hour');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters for station matrix
  const [searchStation, setSearchStation] = useState('');
  const [selectedBorough, setSelectedBorough] = useState('All');
  const [selectedTier, setSelectedTier] = useState('All');

  useEffect(() => {
    fetchDemandForecast(selectedHorizon);
  }, [selectedHorizon]);

  const fetchDemandForecast = async (horizon) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDemandForecasts(horizon);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch demand forecasts.');
    } finally {
      setLoading(false);
    }
  };

  const forecasts = data?.forecasts || [];
  const hourlyTrend = data?.hourly_trend || [];
  const boroughTotals = data?.borough_totals || {};

  const boroughChartData = Object.entries(boroughTotals).map(([borough, volume]) => ({
    borough,
    volume,
  }));

  // Filtered station forecasts
  const filteredForecasts = forecasts.filter((f) => {
    const matchSearch =
      !searchStation ||
      f['Stop Name'].toLowerCase().includes(searchStation.toLowerCase()) ||
      f['Borough'].toLowerCase().includes(searchStation.toLowerCase());

    const matchBorough =
      selectedBorough === 'All' ||
      f['Borough'].toLowerCase() === selectedBorough.toLowerCase();

    const matchTier =
      selectedTier === 'All' || f['Predicted_Congestion'] === selectedTier;

    return matchSearch && matchBorough && matchTier;
  });

  const handleDownloadCSV = () => {
    if (!forecasts.length) return;
    const headers = [
      'Horizon',
      'Hour Ahead',
      'Clock Hour',
      'Station',
      'Borough',
      'Structure',
      'Forecasted Ridership',
      'Congestion Tier',
      'Operational Directive',
    ];

    const rows = filteredForecasts.map((f) => [
      `"${f.Horizon || selectedHorizon}"`,
      `"${f.Hour_Ahead}"`,
      `"${f.Hour}:00"`,
      `"${f['Stop Name']}"`,
      `"${f.Borough}"`,
      `"${f.Structure}"`,
      `"${Math.round(f.Forecasted_Ridership)}"`,
      `"${f.Predicted_Congestion}"`,
      `"${f.Recommended_Action}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `metroflow_demand_forecast_${selectedHorizon.toLowerCase().replace(/\s+/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="ops-panel p-5 bg-gradient-to-r from-[#111827] via-slate-900 to-[#1F293D] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
              REGRESSION PROJECTIONS
            </span>
            <span className="text-xs text-slate-400 font-mono">
              CONTINUOUS RIDERSHIP ESTIMATION
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <TrendingUp size={20} className="text-[#00D4AA]" />
            <span>Passenger Demand Forecasting Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Multi-horizon continuous ridership projections evaluated across 361 stations to proactively mobilize train headway.
          </p>
        </div>

        {/* Horizon Selector */}
        <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400 px-2 font-medium">Horizon:</span>
          {['Next 1 Hour', 'Next 3 Hours', 'Next 24 Hours'].map((h) => (
            <button
              key={h}
              onClick={() => setSelectedHorizon(h)}
              className={`px-3 py-1.5 rounded-md text-xs font-bold font-mono transition ${
                selectedHorizon === h
                  ? 'bg-[#00D4AA] text-[#0B1220] shadow-lg shadow-teal-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {h.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Projected Network Ridership"
          value={data?.total_ridership ? `${Math.round(data.total_ridership).toLocaleString()} riders` : '---'}
          delta={`Across ${selectedHorizon}`}
          deltaType="positive"
          subtext="Cumulative Turnstile Inflows"
          icon={TrendingUp}
          accentColor="#00D4AA"
        />

        <MetricCard
          title="Peak Projected Hub"
          value={data?.peak_station || '149 St - Grand Concourse'}
          delta={`${Math.round(data?.peak_ridership || 2890).toLocaleString()} riders/hr`}
          deltaType="warning"
          subtext="Highest single platform volume"
          icon={MapPin}
          accentColor="#EF4444"
        />

        <MetricCard
          title="Forecasting Horizon"
          value={selectedHorizon}
          delta="Multi-Step Lookahead"
          deltaType="neutral"
          subtext="Random Forest Regressor"
          icon={Clock}
          accentColor="#38BDF8"
        />

        <MetricCard
          title="High Congestion Hubs"
          value={forecasts.filter((f) => f.Predicted_Congestion === 'High').length}
          delta="Proactive Tiers"
          deltaType="warning"
          subtext="Requiring 2-min frequency"
          icon={AlertTriangle}
          accentColor="#F59E0B"
        />
      </div>

      {/* Charts Grid: Hourly Projection Curve + Borough Bar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Projected Hourly Ridership Trend */}
        <div className="ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Clock size={16} className="text-[#38BDF8]" />
                <span>Projected Ridership Trend Curve ({selectedHorizon})</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Mean, peak, and minimum projected passenger volume over future clock hours.
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyTrend}>
                <defs>
                  <linearGradient id="colorTraffic" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#00D4AA" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="Time_Label" stroke="#64748B" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748B" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    fontSize: '11px',
                    color: '#F8FAFC',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="mean"
                  stroke="#00D4AA"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorTraffic)"
                  name="Mean Volume (riders/hr)"
                />
                <Area
                  type="monotone"
                  dataKey="max"
                  stroke="#38BDF8"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  fill="none"
                  name="Peak Station Bound"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Borough Volume Distribution */}
        <div className="ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building size={16} className="text-[#818CF8]" />
                <span>Projected Passenger Volume by Borough</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Cumulative turnstile throughput expected per NYC administrative borough.
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={boroughChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="borough" stroke="#64748B" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748B" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    fontSize: '11px',
                    color: '#F8FAFC',
                  }}
                />
                <Bar dataKey="volume" fill="#38BDF8" radius={[4, 4, 0, 0]} name="Projected Ridership" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Station Forecast Matrix Table */}
      <div className="ops-panel p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <MapPin size={16} className="text-[#00D4AA]" />
              <span>Station Demand Forecast Matrix & Proactive Action Center</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Anticipated turnstile volume, predicted tier, and recommended operational dispatch directive.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={handleDownloadCSV} className="btn-secondary text-xs">
              <Download size={14} />
              <span>Download Forecasts CSV</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by station or street name..."
              value={searchStation}
              onChange={(e) => setSearchStation(e.target.value)}
              className="ops-input pl-8 text-xs py-1.5"
            />
          </div>

          <div>
            <select
              value={selectedBorough}
              onChange={(e) => setSelectedBorough(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              <option value="All">All Boroughs</option>
              <option value="Manhattan">Manhattan</option>
              <option value="Brooklyn">Brooklyn</option>
              <option value="Queens">Queens</option>
              <option value="Bronx">Bronx</option>
            </select>
          </div>

          <div>
            <select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              <option value="All">All Projected Tiers</option>
              <option value="High">🚨 High Congestion Only</option>
              <option value="Medium">⚠️ Medium Congestion Only</option>
              <option value="Low">✅ Low Congestion Only</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto max-h-96">
          <table className="ops-table">
            <thead>
              <tr>
                <th>Hour Ahead</th>
                <th>Clock Hour</th>
                <th>Station Name</th>
                <th>Borough</th>
                <th>Forecasted Ridership</th>
                <th>Projected Tier</th>
                <th>Anticipatory Directive</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredForecasts.slice(0, 50).map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  <td className="font-mono text-xs text-sky-400 font-bold">
                    +{row.Hour_Ahead}h
                  </td>
                  <td className="font-mono text-xs text-slate-300">
                    {row.Hour}:00
                  </td>
                  <td className="font-semibold text-white">
                    {row['Stop Name']}
                  </td>
                  <td className="text-slate-400">{row.Borough}</td>
                  <td className="font-mono font-bold text-white text-xs">
                    {Math.round(row.Forecasted_Ridership).toLocaleString()} riders/hr
                  </td>
                  <td>
                    <StatusBadge status={row.Predicted_Congestion} size="sm" />
                  </td>
                  <td className="text-slate-300 text-xs max-w-xs truncate">
                    {row.Recommended_Action}
                  </td>
                  <td>
                    <button
                      onClick={() => {
                        if (onDispatchAlert) {
                          onDispatchAlert({
                            id: `ALT-FC-${Date.now().toString().slice(-4)}`,
                            station: row['Stop Name'],
                            borough: row.Borough,
                            severity: row.Predicted_Congestion,
                            message: `Anticipatory Demand Surge (+${row.Hour_Ahead}h): Projected ${Math.round(row.Forecasted_Ridership)} riders/hr.`,
                            recommendation: row.Recommended_Action,
                            timestamp: new Date().toLocaleTimeString(),
                            status: 'Active',
                          });
                        }
                        if (onNavigate) onNavigate('alerts-center');
                      }}
                      className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-[#00D4AA] font-medium transition"
                    >
                      Alert &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-3 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
          <strong>Methodology & Limitations:</strong> Regressor is trained on continuous turnstile volume (<code className="text-sky-300">Total_Traffic</code>). Quantile-derived thresholds map continuous ridership into operational tiers (Low: &lt;791, Med: 791-2382, High: &gt;2382 riders/hr). Projections represent synthetic statistical modeling.
        </div>
      </div>
    </div>
  );
}
