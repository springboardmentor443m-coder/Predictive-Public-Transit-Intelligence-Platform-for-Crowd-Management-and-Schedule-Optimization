import React, { useState, useEffect } from 'react';
import {
  Clock,
  Train,
  Gauge,
  Sliders,
  Download,
  AlertCircle,
  CheckCircle,
  FileText,
  Activity,
  Layers,
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import { api } from '../api/client';

export default function ScheduleManagement({ initialLevel = 'High' }) {
  const [selectedLevel, setSelectedLevel] = useState(initialLevel);
  const [scheduleData, setScheduleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Commuter Capacity Simulator Controls
  const [carsPerTrain, setCarsPerTrain] = useState(10);
  const [carCapacity, setCarCapacity] = useState(120);

  useEffect(() => {
    fetchSchedule(selectedLevel);
  }, [selectedLevel]);

  const fetchSchedule = async (level) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getScheduleRecommendation(level);
      setScheduleData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const trainsPerHour = scheduleData?.trains_per_hour || (selectedLevel === 'High' ? 30 : selectedLevel === 'Medium' ? 12 : 6);
  const trainFrequency = scheduleData?.train_frequency || (selectedLevel === 'High' ? 'Every 2 Minutes' : selectedLevel === 'Medium' ? 'Every 5 Minutes' : 'Every 10 Minutes');
  const operationalAction = scheduleData?.operational_action || (selectedLevel === 'High' ? 'Deploy standby trains and increase frequency' : selectedLevel === 'Medium' ? 'Increase monitoring and maintain schedule' : 'Normal schedule sufficient');

  // Throughput Calculations
  const singleTrainCap = carsPerTrain * carCapacity;
  const hourlyLineThroughput = trainsPerHour * singleTrainCap;
  const capacityLoadPct = Math.min(100, Math.round((trainsPerHour / 30) * 100));

  // CSV Export
  const handleExportCSV = () => {
    const rows = [
      ['Congestion Tier', 'Recommended Frequency', 'Trains Per Hour', 'Single Train Capacity', 'Theoretical Hourly Throughput', 'Operational Directive'],
      ['High', 'Every 2 Minutes', '30', `${carsPerTrain * carCapacity}`, `${30 * carsPerTrain * carCapacity}`, 'Deploy standby trains and increase frequency'],
      ['Medium', 'Every 5 Minutes', '12', `${carsPerTrain * carCapacity}`, `${12 * carsPerTrain * carCapacity}`, 'Increase monitoring and maintain schedule'],
      ['Low', 'Every 10 Minutes', '6', `${carsPerTrain * carCapacity}`, `${6 * carsPerTrain * carCapacity}`, 'Normal schedule sufficient'],
    ];

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `metroflow_dispatch_schedule_${selectedLevel.toLowerCase()}.csv`);
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
              OPERATIONAL TIMETABLE REGULATION
            </span>
            <span className="text-xs text-slate-400 font-mono">
              DYNAMIC HEADWAY SCALING
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Clock size={20} className="text-[#00D4AA]" />
            <span>Train Schedule & Operations Optimization Engine</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time translation of predicted crowd levels into recommended train dispatch frequencies and passenger capacity throughput.
          </p>
        </div>

        {/* Congestion Tier Selector */}
        <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400 px-2 font-medium">Select Tier:</span>
          {['High', 'Medium', 'Low'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSelectedLevel(lvl)}
              className={`px-3 py-1.5 rounded-md text-xs font-bold font-mono transition ${
                selectedLevel === lvl
                  ? lvl === 'High'
                    ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30'
                    : lvl === 'Medium'
                    ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/30'
                    : 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {lvl.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Primary KPI Row for Selected Level */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Target Train Frequency"
          value={trainFrequency}
          delta="Automated Headway"
          deltaType="positive"
          subtext={`Under ${selectedLevel} Congestion`}
          icon={Clock}
          accentColor="#00D4AA"
        />

        <MetricCard
          title="Scheduled Trains / Hour"
          value={`${trainsPerHour} Trains/hr`}
          delta={`${hourlyLineThroughput.toLocaleString()} Riders/hr`}
          deltaType={trainsPerHour >= 20 ? 'warning' : 'positive'}
          subtext="Mainline Corridor Target"
          icon={Train}
          accentColor="#38BDF8"
        />

        <MetricCard
          title="Fleet Capacity Load"
          value={`${capacityLoadPct}%`}
          delta={capacityLoadPct > 80 ? 'Peak Surge Fleet' : 'Nominal Fleet'}
          deltaType={capacityLoadPct > 80 ? 'warning' : 'positive'}
          subtext="Relative to 30 train/hr max"
          icon={Gauge}
          accentColor={capacityLoadPct > 80 ? '#EF4444' : '#10B981'}
        />

        <MetricCard
          title="Theoretical Single Train Load"
          value={`${singleTrainCap.toLocaleString()} Riders`}
          delta={`${carsPerTrain} Cars`}
          deltaType="neutral"
          subtext={`@ ${carCapacity} pass/car`}
          icon={Layers}
          accentColor="#818CF8"
        />
      </div>

      {/* Main Operations Directive Card */}
      <div
        className={`ops-panel p-5 border-l-4 ${
          selectedLevel === 'High'
            ? 'border-l-rose-500 bg-rose-500/5'
            : selectedLevel === 'Medium'
            ? 'border-l-amber-500 bg-amber-500/5'
            : 'border-l-emerald-500 bg-emerald-500/5'
        }`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <StatusBadge status={selectedLevel} />
              <span className="text-xs font-mono font-bold text-slate-300">
                ACTIVE DISPATCH DIRECTIVE
              </span>
            </div>
            <h3 className="text-lg font-bold text-white">
              {operationalAction}
            </h3>
            <p className="text-xs text-slate-400">
              Dispatched target frequency: <strong className="text-white">{trainFrequency}</strong>. Standby yard units mobilized for mainline insertion.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button onClick={handleExportCSV} className="btn-secondary text-xs">
              <Download size={14} />
              <span>Export Dispatch Plan CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Capacity Simulation Controls & Throughput Engine */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Interactive Consist Simulator */}
        <div className="ops-panel p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders size={16} className="text-[#00D4AA]" />
              <h3 className="text-sm font-bold text-white">
                Train Consist & Theoretical Line Throughput Simulator
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              PARAMETRIC SIMULATION
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Adjust subway consist length and design car passenger density to evaluate theoretical corridor capacity under different headway frequencies.
          </p>

          <div className="space-y-4 pt-2">
            <div>
              <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
                <span>Train Consist Length (Cars per Train)</span>
                <span className="font-mono text-[#00D4AA] font-bold">{carsPerTrain} Cars</span>
              </div>
              <input
                type="range"
                min="6"
                max="11"
                value={carsPerTrain}
                onChange={(e) => setCarsPerTrain(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#00D4AA]"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-0.5">
                <span>6 Cars (Shuttle)</span>
                <span>8 Cars (Standard)</span>
                <span>10-11 Cars (Full Consist)</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
                <span>Design Passenger Capacity per Car</span>
                <span className="font-mono text-sky-400 font-bold">{carCapacity} Riders</span>
              </div>
              <input
                type="range"
                min="80"
                max="200"
                step="5"
                value={carCapacity}
                onChange={(e) => setCarCapacity(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#38BDF8]"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-0.5">
                <span>80 (Seated comfort)</span>
                <span>120 (Standard rush)</span>
                <span>200 (Crush load maximum)</span>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Corridor Throughput Calculations
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-400">Single Train Capacity:</span>
                <div className="font-mono font-bold text-white text-sm">
                  {singleTrainCap.toLocaleString()} passengers
                </div>
                <div className="text-[10px] text-slate-500">
                  {carsPerTrain} cars &times; {carCapacity} riders
                </div>
              </div>
              <div>
                <span className="text-slate-400">Corridor Hourly Throughput:</span>
                <div className="font-mono font-bold text-[#00D4AA] text-sm">
                  {hourlyLineThroughput.toLocaleString()} riders / hr
                </div>
                <div className="text-[10px] text-slate-500">
                  {trainsPerHour} trains/hr &times; {singleTrainCap} riders
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Master Schedule Matrix Table */}
        <div className="ops-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText size={16} className="text-[#38BDF8]" />
                <span>Standard Dispatch Headway Matrix</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-500">FastAPI Engine</span>
            </div>

            <div className="overflow-x-auto">
              <table className="ops-table text-xs">
                <thead>
                  <tr>
                    <th>Congestion Tier</th>
                    <th>Target Frequency</th>
                    <th>Trains / Hr</th>
                    <th>Hourly Throughput</th>
                    <th>Operational Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className={selectedLevel === 'High' ? 'bg-rose-500/10' : ''}>
                    <td>
                      <StatusBadge status="High" size="sm" />
                    </td>
                    <td className="font-mono font-bold text-white">Every 2 Minutes</td>
                    <td className="font-mono">30</td>
                    <td className="font-mono text-[#00D4AA]">
                      {(30 * singleTrainCap).toLocaleString()} / hr
                    </td>
                    <td className="text-slate-300 text-[11px]">
                      Deploy standby trains and increase frequency
                    </td>
                  </tr>

                  <tr className={selectedLevel === 'Medium' ? 'bg-amber-500/10' : ''}>
                    <td>
                      <StatusBadge status="Medium" size="sm" />
                    </td>
                    <td className="font-mono font-bold text-white">Every 5 Minutes</td>
                    <td className="font-mono">12</td>
                    <td className="font-mono text-amber-400">
                      {(12 * singleTrainCap).toLocaleString()} / hr
                    </td>
                    <td className="text-slate-300 text-[11px]">
                      Increase monitoring and maintain schedule
                    </td>
                  </tr>

                  <tr className={selectedLevel === 'Low' ? 'bg-emerald-500/10' : ''}>
                    <td>
                      <StatusBadge status="Low" size="sm" />
                    </td>
                    <td className="font-mono font-bold text-white">Every 10 Minutes</td>
                    <td className="font-mono">6</td>
                    <td className="font-mono text-emerald-400">
                      {(6 * singleTrainCap).toLocaleString()} / hr
                    </td>
                    <td className="text-slate-300 text-[11px]">
                      Normal schedule sufficient
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4 p-3 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>Operational Disclaimer:</strong> Scheduling recommendations represent simulated project optimization policies. They are not official MTA operating timetables. Physical station architectural capacities are not assumed.
          </div>
        </div>
      </div>
    </div>
  );
}
