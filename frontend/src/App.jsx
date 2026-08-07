/**
 * src/App.jsx
 * -------------
 * The top-level component. Decides WHICH screen to show (login vs the
 * main dashboard) based on whether we have a valid token, and holds the
 * pieces of state that need to be shared between child components.
 */

import { useState } from "react";
import AuthForm from "./components/AuthForm";
import PredictForm from "./components/PredictForm";
import ResultCard from "./components/ResultCard";
import HistoryTable from "./components/HistoryTable";

function App() {
  // We check localStorage right when the app first loads, so a page
  // refresh doesn't log the user out. localStorage persists in the
  // browser even after closing the tab - unlike regular state, which
  // resets to nothing on every page reload.
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [email, setEmail] = useState(() => localStorage.getItem("email"));
  const [result, setResult] = useState(null);
  const [historyRefresh, setHistoryRefresh] = useState(0);

  function handleLoginSuccess(newToken, newEmail) {
    localStorage.setItem("token", newToken);
    localStorage.setItem("email", newEmail);
    setToken(newToken);
    setEmail(newEmail);
  }

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    setToken(null);
    setEmail(null);
    setResult(null);
  }

  function handleNewResult(predictionResult) {
    setResult(predictionResult);
    // Increment a counter to signal HistoryTable it should refetch -
    // a simple, common way to trigger a refresh in a sibling component.
    setHistoryRefresh((prev) => prev + 1);
  }

  // If there's no token, show the login screen and stop here - nothing
  // below this line will render until the user logs in.
  if (!token) {
    return <AuthForm onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <h1 className="font-semibold text-slate-900">Churn Prediction Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">{email}</span>
          <button
            onClick={handleLogout}
            className="text-sm text-slate-500 hover:text-slate-900"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <PredictForm token={token} onResult={handleNewResult} />
        <ResultCard result={result} />
        <HistoryTable token={token} refreshTrigger={historyRefresh} />
      </main>
    </div>
  );
}

export default App;
