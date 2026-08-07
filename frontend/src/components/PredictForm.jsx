/**
 * src/components/PredictForm.jsx
 * ---------------------------------
 * A form matching EXACTLY the fields our backend's CustomerInput schema
 * expects (from Day 2). If you add/remove a field here without matching
 * the backend, you'll get a 422 validation error - a good example of why
 * frontend and backend need to agree on a "contract" (the shape of data).
 */

import { useState } from "react";
import { predictChurn } from "../api";

// Default values so the form starts pre-filled (easier to test/demo than
// an empty form the user has to fill in from scratch every time).
const DEFAULT_CUSTOMER = {
  gender: "Female",
  SeniorCitizen: 0,
  Partner: "Yes",
  Dependents: "No",
  tenure: 2,
  PhoneService: "Yes",
  MultipleLines: "No",
  InternetService: "Fiber optic",
  OnlineSecurity: "No",
  OnlineBackup: "No",
  DeviceProtection: "No",
  TechSupport: "No",
  StreamingTV: "Yes",
  StreamingMovies: "Yes",
  Contract: "Month-to-month",
  PaperlessBilling: "Yes",
  PaymentMethod: "Electronic check",
  MonthlyCharges: 90.5,
  TotalCharges: 181.0,
};

// These match the exact categories our Day 1 LabelEncoder learned from
// the training data - sending anything outside this list would trigger
// our "unknown category" fallback from the bug fix we made earlier.
const OPTIONS = {
  gender: ["Female", "Male"],
  Partner: ["Yes", "No"],
  Dependents: ["Yes", "No"],
  PhoneService: ["Yes", "No"],
  MultipleLines: ["Yes", "No", "No phone service"],
  InternetService: ["DSL", "Fiber optic", "No"],
  OnlineSecurity: ["Yes", "No", "No internet service"],
  OnlineBackup: ["Yes", "No", "No internet service"],
  DeviceProtection: ["Yes", "No", "No internet service"],
  TechSupport: ["Yes", "No", "No internet service"],
  StreamingTV: ["Yes", "No", "No internet service"],
  StreamingMovies: ["Yes", "No", "No internet service"],
  Contract: ["Month-to-month", "One year", "Two year"],
  PaperlessBilling: ["Yes", "No"],
  PaymentMethod: [
    "Electronic check",
    "Mailed check",
    "Bank transfer (automatic)",
    "Credit card (automatic)",
  ],
};

function PredictForm({ token, onResult }) {
  const [customer, setCustomer] = useState(DEFAULT_CUSTOMER);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // One generic handler for ALL fields, instead of writing 19 separate
  // functions. We figure out the field's name from the input itself
  // (e.g. "tenure", "Contract") and update just that one piece of state.
  function handleChange(field, value) {
    setCustomer((prev) => ({ ...prev, [field]: value }));
    // "...prev" copies every existing field, then we overwrite just the
    // one that changed - this is the standard React pattern for updating
    // part of an object in state without accidentally erasing the rest.
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await predictChurn(customer, token);
      onResult(result, customer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-900 mb-4">Customer details</h2>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {/* Dropdown fields - generated from OPTIONS so we don't repeat 15 similar blocks */}
        {Object.entries(OPTIONS).map(([field, choices]) => (
          <div key={field}>
            <label className="block text-xs font-medium text-slate-500 mb-1">{field}</label>
            <select
              value={customer[field]}
              onChange={(e) => handleChange(field, e.target.value)}
              className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-sm"
            >
              {choices.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        ))}

        {/* Numeric fields */}
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Senior Citizen</label>
          <select
            value={customer.SeniorCitizen}
            onChange={(e) => handleChange("SeniorCitizen", Number(e.target.value))}
            className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-sm"
          >
            <option value={0}>No</option>
            <option value={1}>Yes</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Tenure (months)</label>
          <input
            type="number" min="0" required
            value={customer.tenure}
            onChange={(e) => handleChange("tenure", Number(e.target.value))}
            className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Monthly Charges ($)</label>
          <input
            type="number" min="0" step="0.01" required
            value={customer.MonthlyCharges}
            onChange={(e) => handleChange("MonthlyCharges", Number(e.target.value))}
            className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Total Charges ($)</label>
          <input
            type="number" min="0" step="0.01" required
            value={customer.TotalCharges}
            onChange={(e) => handleChange("TotalCharges", Number(e.target.value))}
            className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-sm"
          />
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg mt-4">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="mt-5 bg-slate-900 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition"
      >
        {loading ? "Predicting..." : "Predict churn risk"}
      </button>
    </form>
  );
}

export default PredictForm;
