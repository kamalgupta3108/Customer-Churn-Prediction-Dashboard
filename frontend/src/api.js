/**
 * src/api.js
 * -----------
 * Every function here talks to our FastAPI backend. Keeping all API calls
 * in ONE file (instead of scattered across every component) means: if the
 * backend URL changes, or we need to add error handling in one place, we
 * only touch this file - no component needs to know HOW we talk to the
 * server, only that these functions exist.
 *
 * fetch() is the browser's built-in way to make HTTP requests - like curl,
 * but from JavaScript running in the browser.
 */

const API_BASE_URL = "http://localhost:8000";

/**
 * Register a new user account.
 */
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

/**
 * Log in and get back a JWT token (the "wristband" from Day 3).
 *
 * Note: our backend's /auth/login endpoint expects FORM data (not JSON) -
 * that's a FastAPI/OAuth2 convention we set up on the backend. URLSearchParams
 * builds exactly that format for us.
 */
export async function loginUser(email, password) {
  const formData = new URLSearchParams();
  formData.append("username", email); // backend treats "username" field as email
  formData.append("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Incorrect email or password");
  }
  return response.json(); // { access_token, token_type }
}

/**
 * Get a churn prediction for one customer. Requires a valid token -
 * this is a PROTECTED endpoint, remember from Day 3.
 */
export async function predictChurn(customerData, token) {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`, // the "show your wristband" step
    },
    body: JSON.stringify(customerData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Prediction failed");
  }
  return response.json();
}

/**
 * Fetch this user's past predictions.
 */
export async function getHistory(token) {
  const response = await fetch(`${API_BASE_URL}/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error("Failed to load history");
  }
  return response.json();
}
