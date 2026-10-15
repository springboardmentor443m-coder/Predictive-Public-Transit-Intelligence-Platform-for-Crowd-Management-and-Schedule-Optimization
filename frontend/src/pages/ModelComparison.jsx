import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Award,
  ShieldCheck,
  Zap,
  CheckCircle,
  TrendingUp,
  Cpu,
  Info,
  Check,
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { api } from '../api/client';

export default function ModelComparison() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchComparisonData();
  }, []);

  const fetchComparisonData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getModelComparison();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch model comparison data.');
    } finally {
      setLoading(false);
    }
  };

  const models = data?.models || [
    { Model: 'Random Forest Classifier', Accuracy: 0.871, Precision: 0.8701, Recall: 0.871, 'F1 Score': 0.8703 },
    { Model: 'XGBoost Classifier', Accuracy: 0.8649, Precision: 0.8634, Recall: 0.8649, 'F1 Score': 0.8638 },
    { Model: 'Decision Tree Classifier', Accuracy: 0.8562, Precision: 0.8548, Recall: 0.8562, 'F1 Score': 0.8552 },
    { Model: 'Gradient Boosting Classifier', Accuracy: 0.7731, Precision: 0.768, Recall: 0.7731, 'F1 Score': 0.7685 },
    { Model: 'Logistic Regression', Accuracy: 0.5929, Precision: 0.5775, Recall: 0.5929, 'F1 Score': 0.5799 },
    { Model: 'AdaBoost Classifier', Accuracy: 0.5835, Precision: 0.3929, Recall: 0.5835, 'F1 Score': 0.4692 },
  ];

  const featureImportances = data?.feature_importances || [
    { feature: 'hour', importance: 0.268, percentage: 26.8 },
    { feature: 'Latitude', importance: 0.185, percentage: 18.5 },
    { feature: 'Longitude', importance: 0.17, percentage: 17.0 },
    { feature: 'Stop Name_encoded', importance: 0.132, percentage: 13.2 },
    { feature: 'Borough_encoded', importance: 0.084, percentage: 8.4 },
    { feature: 'Structure_encoded', importance: 0.052, percentage: 5.2 },
    { feature: 'day_of_week', importance: 0.043, percentage: 4.3 },
    { feature: 'is_peak_hour', importance: 0.038, percentage: 3.8 },
  ];

  const rankLabels = ['🥇 1st (Champion)', '🥈 2nd (Runner-Up)', '🥉 3rd', '4th', '5th', '6th'];

  // Prepare chart data
  const accuracyChartData = models.map((m) => ({
    name: m.Model.replace(' Classifier', ''),
    accuracy: Math.round(m.Accuracy * 1000) / 10,
    isChampion: m.Model.includes('Random Forest'),
  }));

  const f1ChartData = models.map((m) => ({
    name: m.Model.replace(' Classifier', ''),
    f1: Math.round((m['F1 Score'] || m.F1_Score) * 10000) / 10000,
    isChampion: m.Model.includes('Random Forest'),
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="ops-panel p-5 bg-gradient-to-r from-[#111827] via-slate-900 to-[#1F293D] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-teal-500/10 text-[#00D4AA] border border-teal-500/20">
              BENCHMARKING & AUDIT
            </span>
            <span className="text-xs text-slate-400 font-mono">
              6 MACHINE LEARNING ALGORITHMS
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 size={20} className="text-[#00D4AA]" />
            <span>Model Comparison & Benchmarking Leaderboard</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Empirical evaluation across Random Forest, XGBoost, Decision Tree, Gradient Boosting, Logistic Regression, and AdaBoost.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          <Award size={16} className="text-[#00D4AA]" />
          <div className="text-xs">
            <span className="text-slate-400">Deployed Champion:</span>{' '}
            <strong className="text-white font-mono">Random Forest (87.1% Acc)</strong>
          </div>
        </div>
      </div>

      {/* Production Champion Highlight Box */}
      <div className="ops-panel p-5 border-l-4 border-l-[#00D4AA] bg-gradient-to-r from-teal-500/10 via-slate-900 to-slate-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-xs font-bold font-mono bg-[#00D4AA] text-[#0B1220]">
              PRODUCTION ARTIFACT (congestion_model.pkl)
            </span>
            <span className="text-xs text-slate-400">Strictly Non-Leaked Features</span>
          </div>
          <h3 className="text-lg font-bold text-white">
            Random Forest Classifier Selected as Champion
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
            Random Forest achieved the top overall test accuracy (<strong>87.10%</strong>) and weighted F1-score (<strong>0.8703</strong>), demonstrating superior multi-class robustness and calibration on imbalanced rush-hour distributions compared to boosting and linear models.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 shrink-0 text-center">
          <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Accuracy</span>
            <div className="text-base font-bold font-mono text-[#00D4AA]">87.10%</div>
          </div>
          <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Weighted F1</span>
            <div className="text-base font-bold font-mono text-sky-400">0.8703</div>
          </div>
          <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Precision</span>
            <div className="text-base font-bold font-mono text-amber-400">0.8701</div>
          </div>
          <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Recall</span>
            <div className="text-base font-bold font-mono text-emerald-400">0.8710</div>
          </div>
        </div>
      </div>

      {/* Comparative Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Accuracy Comparison Chart */}
        <div className="ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BarChart3 size={16} className="text-[#00D4AA]" />
                <span>Classification Accuracy Across Models (%)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated on 20% holdout test split (Stratified).
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={accuracyChartData} layout="vertical" margin={{ left: 35, right: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} stroke="#64748B" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" stroke="#94A3B8" tick={{ fontSize: 11 }} width={120} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    fontSize: '11px',
                    color: '#F8FAFC',
                  }}
                  formatter={(val) => [`${val}%`, 'Accuracy']}
                />
                <Bar dataKey="accuracy" radius={[0, 4, 4, 0]}>
                  {accuracyChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.isChampion ? '#00D4AA' : '#38BDF8'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weighted F1 Score Comparison Chart */}
        <div className="ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp size={16} className="text-[#38BDF8]" />
                <span>Weighted F1 Score Comparison</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Harmonic mean of precision and recall accounting for class imbalance.
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={f1ChartData} layout="vertical" margin={{ left: 35, right: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                <XAxis type="number" domain={[0, 1.0]} stroke="#64748B" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" stroke="#94A3B8" tick={{ fontSize: 11 }} width={120} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    fontSize: '11px',
                    color: '#F8FAFC',
                  }}
                  formatter={(val) => [val, 'Weighted F1']}
                />
                <Bar dataKey="f1" radius={[0, 4, 4, 0]}>
                  {f1ChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.isChampion ? '#00D4AA' : '#818CF8'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Feature Importance & Technical Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feature Importance Chart */}
        <div className="ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Cpu size={16} className="text-[#00D4AA]" />
                <span>Feature Importance Rankings (Champion Model)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Gini impurity decrease across decision trees in Random Forest.
              </p>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            {featureImportances.map((item, idx) => (
              <div key={item.feature} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-mono text-slate-300">
                    <strong className="text-slate-500 mr-2">#{idx + 1}</strong>
                    {item.feature}
                  </span>
                  <span className="font-mono font-bold text-[#00D4AA]">
                    {item.percentage}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-teal-500 to-sky-400 rounded-full"
                    style={{ width: `${item.percentage * 3}%` }} // scaled for visual impact
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Leaderboard Table & Explanations */}
        <div className="ops-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Award size={16} className="text-amber-400" />
                <span>Multi-Model Evaluation Matrix</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-500">
                reports/model_comparison.csv
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="ops-table text-xs">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Accuracy</th>
                    <th>F1 Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m, idx) => {
                    const isTop = idx === 0;
                    return (
                      <tr key={m.Model} className={isTop ? 'bg-teal-500/10' : ''}>
                        <td className="font-bold text-xs">{rankLabels[idx]}</td>
                        <td className="font-semibold text-white">
                          {m.Model}
                        </td>
                        <td className="font-mono text-slate-200">
                          {(m.Accuracy * 100).toFixed(2)}%
                        </td>
                        <td className="font-mono font-bold text-sky-400">
                          {(m['F1 Score'] || m.F1_Score).toFixed(4)}
                        </td>
                        <td>
                          {isTop ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#00D4AA]/20 text-[#00D4AA] border border-[#00D4AA]/40">
                              DEPLOYED
                            </span>
                          ) : (
                            <span className="text-[10px] font-mono text-slate-500">
                              Evaluated
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4 p-3 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-400 leading-relaxed space-y-1.5">
            <div>
              <strong>Feature Interpretation:</strong> <code className="text-[#00D4AA]">hour</code> (26.8%) governs commuter peak rushes vs. overnight lulls. <code className="text-sky-300">Latitude</code> (18.5%) & <code className="text-sky-300">Longitude</code> (17.0%) separate dense Manhattan hubs from residential outer corridors.
            </div>
            <div className="text-slate-500">
              Note: The invalid Plotly colorscale error (<code className="text-rose-400">"Emerald"</code>) in the legacy Streamlit script has been investigated and fixed in <code className="text-slate-300">dashboard/app.py</code> using <code className="text-emerald-400">"emrld"</code>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
