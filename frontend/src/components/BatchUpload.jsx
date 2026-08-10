/**
 * src/components/BatchUpload.jsx
 * ---------------------------------
 * Lets a user upload a CSV of many customers, and shows LIVE progress
 * while the backend processes it in the background (remember Day 4's
 * "smart waiter" pattern - the upload returns instantly, then we poll).
 *
 * NEW CONCEPT: setInterval - a JavaScript function that repeats an action
 * every N milliseconds, until we explicitly stop it with clearInterval.
 * We use this to check "how's my batch doing?" every 1.5 seconds without
 * the user needing to click "refresh" themselves.
 */

import { useState, useRef, useEffect } from "react";
import { uploadBatch, getBatchStatus } from "../api";

function BatchUpload({ token, onBatchComplete }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null); // null | {status, total_rows, processed_rows, failed_rows}
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  // useRef gives us a value that persists across renders WITHOUT causing
  // a re-render when it changes (unlike useState). We use it here to hold
  // onto the interval's ID, so we can cancel it later with clearInterval.
  const pollIntervalRef = useRef(null);

  function stopPolling() {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }

  // Safety net: if this component EVER truly unmounts (e.g. the user logs
  // out entirely while a batch is running), make sure we don't leave an
  // interval running forever in the background, silently hitting the API
  // every 1.5 seconds for no one. The empty dependency array means this
  // cleanup only runs once, when the component finally goes away for good.
  useEffect(() => {
    return () => stopPolling();
  }, []);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setUploading(true);
    setStatus(null);

    try {
      const { batch_id } = await uploadBatch(file, token);

      // Start polling immediately - check every 1.5 seconds
      pollIntervalRef.current = setInterval(async () => {
        try {
          const currentStatus = await getBatchStatus(batch_id, token);
          setStatus(currentStatus);

          // Once the backend says it's done (either way), stop polling -
          // otherwise we'd keep hitting the API forever, wastefully.
          if (currentStatus.status === "completed" || currentStatus.status === "failed") {
            stopPolling();
            setUploading(false);
            if (currentStatus.status === "completed") {
              onBatchComplete(); // tells App.jsx to refresh history/dashboard
            }
          }
        } catch (pollError) {
          stopPolling();
          setUploading(false);
          setError("Lost connection while checking batch progress.");
        }
      }, 1500);
    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  }

  const progressPercent = status && status.total_rows > 0
    ? Math.round((status.processed_rows / status.total_rows) * 100)
    : 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-900 mb-1">Batch upload</h2>
      <p className="text-xs text-slate-500 mb-4">
        Upload a CSV with the same columns as a single prediction, for many customers at once.
      </p>

      <form onSubmit={handleUpload} className="flex items-center gap-3">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
          className="text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
        />
        <button
          type="submit"
          disabled={!file || uploading}
          className="bg-slate-900 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition whitespace-nowrap"
        >
          {uploading ? "Processing..." : "Upload"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg mt-4">{error}</p>}

      {status && (
        <div className="mt-5">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>
              {status.status === "completed" ? "Completed" : "Processing"} - {status.processed_rows} / {status.total_rows} rows
              {status.failed_rows > 0 && ` (${status.failed_rows} skipped)`}
            </span>
            <span>{progressPercent}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${status.status === "completed" ? "bg-emerald-500" : "bg-slate-900"}`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          {status.status === "completed" && (
            <p className="text-xs text-emerald-600 mt-2">
              Done! Check the dashboard and history below for results.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default BatchUpload;
