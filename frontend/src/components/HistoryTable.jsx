/**
 * src/components/HistoryTable.jsx
 * ----------------------------------
 * Shows past predictions, fetched from our /history endpoint.
 *
 * useEffect is a new hook - it runs code automatically when the component
 * first appears on screen (or when specific values change). Here we use
 * it to fetch history data ONCE when this component mounts, without the
 * user needing to click anything.
 */

import { useState, useEffect } from "react";
import { getHistory } from "../api";

function HistoryTable({ token, refreshTrigger }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      try {
        const data = await getHistory(token);
        // Show most recent first
        setHistory(data.reverse());
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
    // The array below tells React: "re-run this effect whenever `token`
    // or `refreshTrigger` changes." We use refreshTrigger (a number that
    // increments after each new prediction) to make history refetch
    // automatically right after a new prediction is made.
  }, [token, refreshTrigger]);

  if (loading) return <p className="text-sm text-slate-500 mt-6">Loading history...</p>;
  if (error) return <p className="text-sm text-red-600 mt-6">{error}</p>;
  if (history.length === 0) {
    return <p className="text-sm text-slate-400 mt-6">No predictions yet - try one above.</p>;
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mt-6">
      <h2 className="text-lg font-semibold text-slate-900 mb-4">Prediction history</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
            <th className="pb-2 font-medium">Contract</th>
            <th className="pb-2 font-medium">Tenure</th>
            <th className="pb-2 font-medium">Monthly $</th>
            <th className="pb-2 font-medium">Churn %</th>
            <th className="pb-2 font-medium">Risk</th>
          </tr>
        </thead>
        <tbody>
          {history.map((row) => (
            <tr key={row.id} className="border-b border-slate-100 last:border-0">
              <td className="py-2 text-slate-700">{row.contract}</td>
              <td className="py-2 text-slate-700">{row.tenure} mo</td>
              <td className="py-2 text-slate-700">${row.monthly_charges.toFixed(2)}</td>
              <td className="py-2 text-slate-700">{Math.round(row.churn_probability * 100)}%</td>
              <td className="py-2">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    row.risk_level === "High"
                      ? "bg-red-50 text-red-700"
                      : row.risk_level === "Medium"
                      ? "bg-amber-50 text-amber-700"
                      : "bg-emerald-50 text-emerald-700"
                  }`}
                >
                  {row.risk_level}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default HistoryTable;
