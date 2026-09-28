/**
 * frontend/js/api.js
 * Thin wrapper around fetch() for talking to the Flask REST API.
 * Keeps the JWT in localStorage under "diet_planner_token" and attaches
 * it as a Bearer token on every authenticated request.
 */

const API_BASE = ""; // same-origin: Flask serves both API and frontend

const Api = {
  getToken() {
    return localStorage.getItem("diet_planner_token");
  },
  setToken(token) {
    localStorage.setItem("diet_planner_token", token);
  },
  clearToken() {
    localStorage.removeItem("diet_planner_token");
    localStorage.removeItem("diet_planner_user");
  },
  setUser(user) {
    localStorage.setItem("diet_planner_user", JSON.stringify(user));
  },
  getUser() {
    const raw = localStorage.getItem("diet_planner_user");
    return raw ? JSON.parse(raw) : null;
  },
  isLoggedIn() {
    return !!this.getToken();
  },
  requireLogin() {
    if (!this.isLoggedIn()) {
      window.location.href = "/pages/login.html";
    }
  },

  async request(path, { method = "GET", body, isForm = false } = {}) {
    const headers = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (!isForm && body) headers["Content-Type"] = "application/json";

    const response = await fetch(API_BASE + path, {
      method,
      headers,
      body: isForm ? body : body ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401) {
      this.clearToken();
      window.location.href = "/pages/login.html";
      return null;
    }

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return { ok: response.ok, raw: response };
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed");
    }
    return data;
  },

  register(name, email, password) {
    return this.request("/api/register", { method: "POST", body: { name, email, password } });
  },
  login(email, password) {
    return this.request("/api/login", { method: "POST", body: { email, password } });
  },
  logout() {
    return this.request("/api/logout", { method: "POST" });
  },
  getProfile() {
    return this.request("/api/profile");
  },
  updateProfile(fields) {
    return this.request("/api/profile", { method: "PUT", body: fields });
  },
  generatePlan(overrides = {}) {
    return this.request("/api/generate-plan", { method: "POST", body: overrides });
  },
  listPlans() {
    return this.request("/api/plans");
  },
  getPlan(id) {
    return this.request(`/api/plans/${id}`);
  },
  deletePlan(id) {
    return this.request(`/api/plans/${id}`, { method: "DELETE" });
  },
  listFiles() {
    return this.request("/api/files");
  },
  uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request("/api/upload", { method: "POST", body: formData, isForm: true });
  },
  deleteFile(id) {
    return this.request(`/api/files/${id}`, { method: "DELETE" });
  },
};
