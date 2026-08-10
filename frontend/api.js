// Vite exposes any env variable prefixed with VITE_ to our frontend code
// via import.meta.env. This lets us point at localhost during local
// development, but at a real deployed backend URL once we deploy - all
// without changing any code, just an environment variable at build time.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function registerUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Registration failed");
  }
  return response.json();
}

export async function loginUser(email, password) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });
  if (!response.ok) throw new Error("Incorrect email or password");
  return response.json();
}

export async function predictChurn(customerData, token) {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(customerData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Prediction failed");
  }
  return response.json();
}

export async function getHistory(token) {
  const response = await fetch(`${API_BASE_URL}/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Failed to load history");
  return response.json();
}

/**
 * NEW for Day 7: upload a CSV file for batch prediction.
 * Note we do NOT set Content-Type here - the browser automatically sets
 * the correct "multipart/form-data" header (with the right boundary
 * string) when we send a FormData object. Setting it manually ourselves
 * would actually break the upload.
 */
export async function uploadBatch(file, token) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict-batch`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }
  return response.json();
}

/**
 * NEW for Day 7: check on a batch's progress.
 */
export async function getBatchStatus(batchId, token) {
  const response = await fetch(`${API_BASE_URL}/batch-status/${batchId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Failed to fetch batch status");
  return response.json();
}
