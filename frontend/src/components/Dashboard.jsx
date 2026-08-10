/**
 * src/components/Dashboard.jsx
 * -------------------------------
 * Turns your prediction history into visual charts using Recharts.
 *
 * KEY IDEA: Recharts components don't calculate anything themselves - YOU
 * calculate the numbers first (in plain JavaScript), then hand Recharts a
 * simple array of {name, value} style objects, and it draws the shapes.
 * The hard part is almost always "shaping my data correctly," not the
 * charting library itself.
 */

import { useState, useEffect } from "react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { getHistory } from "../api";

// Consistent colors so "High" is always red everywhere in the dashboard,
// not just coincidentally the first color in some default palette.
const RISK_COLORS = { High: "#ef4444", Medium: "#f59e0b", Low: "#10b981" };

function Dashboard({ token, refreshTrigger }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await getHistory(token);
      setHistory(data);
      setLoading(false);
    }
    load();
  }, [token, refreshTrigger]);

  if (loading) return <p className="text-sm text-slate-500">Loading dashboard...</p>;

  if (history.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <p className="text-sm text-slate-400">
          No predictions yet. Run a prediction or upload a batch to see your dashboard.
        </p>
      </div>
    );
  }

  // --- Calculate summary numbers from the raw history array ---
  const totalPredictions = history.length;
  const churnRate = (
    history.reduce((sum, r) => sum + r.churn_probability, 0) / totalPredictions
  ) * 100;

  // Count how many fall into each risk bucket - this is the classic
  // "reduce a list into a summary object" pattern you'll use constantly
  // once you're comfortable with JavaScript arrays.
  const riskCounts = history.reduce(
    (acc, r) => {
      acc[r.risk_level] = (acc[r.risk_level] || 0) + 1;
      return acc;
    },
    { High: 0, Medium: 0, Low: 0 }
  );

  // Recharts' PieChart wants an array like [{name: "High", value: 12}, ...]
  const pieData = Object.entries(riskCounts)
    .map(([name, value]) => ({ name, value }))
    .filter((d) => d.value > 0);

  // Group predictions by contract type, to show a bar chart of average
  // churn risk per contract type - a genuinely useful business view.
  const byContract = {};
  history.forEach((r) => {
    if (!byContract[r.contract]) byContract[r.contract] = { total: 0, count: 0 };
    byContract[r.contract].total += r.churn_probability;
    byContract[r.contract].count += 1;
  });
  const contractData = Object.entries(byContract).map(([contract, { total, count }]) => ({
    contract,
    avgChurnPercent: Math.round((total / count) * 100),
  }));

  return (
    <div className="space-y-6">
      {/* Summary stat cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <p className="text-xs text-slate-500 mb-1">Total predictions</p>
          <p className="text-2xl font-bold text-slate-900">{totalPredictions}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <p className="text-xs text-slate-500 mb-1">Average churn probability</p>
          <p className="text-2xl font-bold text-slate-900">{churnRate.toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <p className="text-xs text-slate-500 mb-1">High risk customers</p>
          <p className="text-2xl font-bold text-red-600">{riskCounts.High}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Risk distribution pie chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Risk distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                {/* We loop through our own data to assign each slice a
                    color matching RISK_COLORS - Recharts doesn't know
                    "High" should be red on its own, we tell it explicitly. */}
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Average churn risk by contract type - bar chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Avg. churn % by contract type</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={contractData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="contract" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} unit="%" />
              <Tooltip />
              <Bar dataKey="avgChurnPercent" fill="#1e293b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
