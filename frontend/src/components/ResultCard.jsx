/**
 * src/components/ResultCard.jsx
 * --------------------------------
 * Displays a prediction result. Pure "presentation" component - it just
 * receives data via props and displays it, no logic of its own. This kind
 * of simple, "dumb" component is easy to test and reuse.
 */

// A small helper - not a component, just a plain function that picks
// colors based on the risk level, keeping the JSX below cleaner.
function riskColor(riskLevel) {
  if (riskLevel === "High") return "bg-red-50 text-red-700 border-red-200";
  if (riskLevel === "Medium") return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-emerald-50 text-emerald-700 border-emerald-200";
}

function ResultCard({ result }) {
  if (!result) return null;

  const percent = Math.round(result.churn_probability * 100);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mt-6">
      <h2 className="text-lg font-semibold text-slate-900 mb-4">Prediction result</h2>

      <div className="flex items-center gap-4 mb-5">
        <div className={`px-4 py-2 rounded-lg border text-sm font-semibold ${riskColor(result.risk_level)}`}>
          {result.risk_level} risk
        </div>
        <div className="text-2xl font-bold text-slate-900">{percent}%</div>
        <div className="text-sm text-slate-500">churn probability</div>
      </div>

      {/* A simple visual bar - width driven directly by the percentage */}
      <div className="w-full bg-slate-100 rounded-full h-2 mb-5">
        <div
          className={`h-2 rounded-full ${percent >= 70 ? "bg-red-500" : percent >= 40 ? "bg-amber-500" : "bg-emerald-500"}`}
          style={{ width: `${percent}%` }}
        />
      </div>

      <div>
        <p className="text-xs font-medium text-slate-500 mb-2">Top factors driving this prediction</p>
        <div className="flex flex-wrap gap-2">
          {result.top_risk_factors.map((factor) => (
            <span
              key={factor}
              className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full"
            >
              {factor}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ResultCard;
