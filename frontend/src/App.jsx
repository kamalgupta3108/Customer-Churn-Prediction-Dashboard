import { useState } from "react";
import AuthForm from "./components/AuthForm";
import PredictForm from "./components/PredictForm";
import ResultCard from "./components/ResultCard";
import HistoryTable from "./components/HistoryTable";
import BatchUpload from "./components/BatchUpload";
import Dashboard from "./components/Dashboard";

const TABS = [
  { id: "predict", label: "Single Prediction" },
  { id: "batch", label: "Batch Upload" },
  { id: "dashboard", label: "Dashboard" },
];

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [email, setEmail] = useState(() => localStorage.getItem("email"));
  const [result, setResult] = useState(null);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [activeTab, setActiveTab] = useState("predict");

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
    setHistoryRefresh((prev) => prev + 1);
  }

  function handleBatchComplete() {
    setHistoryRefresh((prev) => prev + 1);
  }

  if (!token) {
    return <AuthForm onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <h1 className="font-semibold text-slate-900">Churn Prediction Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">{email}</span>
          <button onClick={handleLogout} className="text-sm text-slate-500 hover:text-slate-900">Log out</button>
        </div>
      </header>

      <div className="bg-white border-b border-slate-200 px-6">
        <div className="max-w-4xl mx-auto flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition ${
                activeTab === tab.id
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* IMPORTANT: all three tabs stay MOUNTED at all times - we just
            hide the inactive ones with CSS (display: none via the
            "hidden" class). This is deliberate: if we unmounted BatchUpload
            whenever its tab wasn't active, switching tabs mid-upload would
            destroy its state (including the running progress-polling
            interval), making an in-progress batch look like it "stopped" -
            even though the backend was still processing it correctly the
            whole time. Keeping it mounted means polling keeps running,
            and the progress bar picks up right where you left it. */}
        <div className={activeTab === "predict" ? "" : "hidden"}>
          <PredictForm token={token} onResult={handleNewResult} />
          <ResultCard result={result} />
          <HistoryTable token={token} refreshTrigger={historyRefresh} />
        </div>

        <div className={activeTab === "batch" ? "" : "hidden"}>
          <BatchUpload token={token} onBatchComplete={handleBatchComplete} />
          <HistoryTable token={token} refreshTrigger={historyRefresh} />
        </div>

        <div className={activeTab === "dashboard" ? "" : "hidden"}>
          <Dashboard token={token} refreshTrigger={historyRefresh} />
        </div>
      </main>
    </div>
  );
}

export default App;
