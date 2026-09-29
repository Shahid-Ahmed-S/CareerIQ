/**
 * api.js
 * Uses sessionStorage so each tab/window keeps its own login session.
 * Multiple users can be logged in simultaneously in different windows.
 */
const API = (() => {
  const BASE = "/api";

  // sessionStorage = isolated per tab. localStorage = shared across all tabs.
  const store = {
    get: k  => sessionStorage.getItem(k) || localStorage.getItem(k),
    set: (k, v) => { sessionStorage.setItem(k, v); },
    del: k  => { sessionStorage.removeItem(k); localStorage.removeItem(k); },
    clear: () => { sessionStorage.clear(); }
  };

  function token() { return store.get("access_token"); }

  function headers() {
    const h = { "Content-Type": "application/json" };
    const t = token();
    if (t) h["Authorization"] = "Bearer " + t;
    return h;
  }

  async function request(method, path, body) {
    const opts = { method, headers: headers() };
    if (body !== undefined) opts.body = JSON.stringify(body);
    let res = await fetch(BASE + path, opts);
    if (res.status === 401) {
      const ok = await tryRefresh();
      if (ok) {
        opts.headers = headers();
        res = await fetch(BASE + path, opts);
      } else {
        logout();
        throw new Error("Session expired. Please sign in again.");
      }
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || data.message || "HTTP " + res.status);
    return data;
  }

  async function tryRefresh() {
    const rt = store.get("refresh_token");
    if (!rt) return false;
    try {
      const r = await fetch(BASE + "/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + rt }
      });
      if (!r.ok) return false;
      const d = await r.json();
      store.set("access_token", d.access_token);
      return true;
    } catch { return false; }
  }

  function logout() {
    store.clear();
    window.location.href = "/login";
  }

  function saveSession(data) {
    store.set("access_token",  data.access_token);
    store.set("refresh_token", data.refresh_token);
    store.set("user",          JSON.stringify(data.user));
  }

  return {
    get:    (p)    => request("GET",    p),
    post:   (p, b) => request("POST",   p, b),
    put:    (p, b) => request("PUT",    p, b),
    patch:  (p, b) => request("PATCH",  p, b),
    delete: (p)    => request("DELETE", p),
    logout,
    saveSession,
    getUser: () => { try { return JSON.parse(store.get("user") || "null"); } catch { return null; } },
    isLoggedIn: () => !!store.get("access_token"),
  };
})();
window.API = API;
