/**
 * src/components/AuthForm.jsx
 * -----------------------------
 * Handles BOTH login and registration in one component, toggled by a
 * button. This is a common pattern - rather than two separate pages,
 * one form that switches "mode".
 */

import { useState } from "react";
import { registerUser, loginUser } from "../api";

// "onLoginSuccess" is a PROP - a value passed IN from the parent component
// (App.jsx). This is how a child component "reports back" to its parent:
// it doesn't manage the app's overall state itself, it just calls this
// function and lets App.jsx decide what happens next (in our case,
// storing the token and switching to the dashboard view).
function AuthForm({ onLoginSuccess }) {
  // Each useState call is a separate piece of "memory" for this component.
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // This function runs when the form is submitted (button clicked or Enter pressed)
  async function handleSubmit(e) {
    e.preventDefault(); // stops the browser's default "reload the page" behavior
    setError("");
    setLoading(true);

    try {
      if (isRegisterMode) {
        await registerUser(email, password);
        // After successful registration, immediately log them in too,
        // so they don't have to type their password twice in a row.
      }
      const { access_token } = await loginUser(email, password);
      onLoginSuccess(access_token, email);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 w-full max-w-sm">
        <h1 className="text-xl font-semibold text-slate-900 mb-1">
          Churn Prediction Dashboard
        </h1>
        <p className="text-sm text-slate-500 mb-6">
          {isRegisterMode ? "Create an account" : "Log in to continue"}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              // Every keystroke updates state, and React re-renders the input
              // with the new value - this is called a "controlled input."
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              placeholder="At least 8 characters"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition"
          >
            {loading ? "Please wait..." : isRegisterMode ? "Create account" : "Log in"}
          </button>
        </form>

        <button
          onClick={() => setIsRegisterMode(!isRegisterMode)}
          className="mt-4 text-sm text-slate-500 hover:text-slate-900 w-full text-center"
        >
          {isRegisterMode
            ? "Already have an account? Log in"
            : "New here? Create an account"}
        </button>
      </div>
    </div>
  );
}

export default AuthForm;
