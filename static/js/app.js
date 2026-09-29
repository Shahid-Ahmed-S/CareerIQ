// ── Auth helpers ──────────────────────────────────────────────
function requireAuth() {
  if (!API.isLoggedIn()) window.location.href = "/login";
}

async function loadUserChip() {
  let user = API.getUser();
  if (!user) {
    try {
      const r = await API.get("/auth/me");
      user = r.user;
      sessionStorage.setItem("user", JSON.stringify(user));
      checkVerifyBanner(r);
    } catch { return; }
  } else {
    API.get("/auth/me").then(r => {
      sessionStorage.setItem("user", JSON.stringify(r.user));
      checkVerifyBanner(r);
    }).catch(() => {});
  }
  const ne = document.getElementById("userName");
  const ae = document.getElementById("userAvatar");
  const aw = document.getElementById("userAvatarWrap");
  if (ne) ne.textContent = user.full_name || user.email;
  if (user.avatar_url && aw) {
    aw.innerHTML = `<img src="${user.avatar_url}" class="avatar-img" alt="avatar"/>`;
  } else if (ae) {
    ae.textContent = (user.full_name || "?")[0].toUpperCase();
  }
  loadCounts();
  initSocket();
}

async function loadCounts() {
  try {
    const [msg, notif] = await Promise.all([
      API.get("/messages/unread-count"),
      API.get("/notifications/unread-count"),
    ]);
    const mb = document.getElementById("msgBadge");
    if (mb) { mb.textContent = msg.unread; mb.style.display = msg.unread > 0 ? "inline-flex" : "none"; }
    if (typeof updateNotifCount === "function") updateNotifCount(notif.count);
  } catch {}
}

// ── SocketIO ──────────────────────────────────────────────────
let _socket = null;

function initSocket() {
  if (_socket) return;
  const token = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  if (!token) return;
  try {
    _socket = io({ auth: { token } });
    _socket.on("connect", () => console.log("Socket connected"));
    _socket.on("notification", (data) => {
      showToast(data.title, data.body);
      loadCounts();
    });
    _socket.on("new_message", (data) => {
      if (typeof onNewMessage === "function") onNewMessage(data);
      loadCounts();
    });
    _socket.on("user_typing", (data) => {
      if (typeof onTyping === "function") onTyping(data);
    });
    window._socket = _socket;
  } catch(e) { console.warn("Socket init failed:", e); }
}

function getSocket() { return _socket || window._socket; }

// ── Toast notifications ───────────────────────────────────────
function showToast(title, body) {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed;bottom:24px;right:24px;z-index:9999;
    background:var(--bg2);border:1px solid var(--border);
    border-radius:var(--radius-lg);padding:14px 18px;
    box-shadow:0 8px 32px rgba(0,0,0,.4);
    display:flex;gap:12px;align-items:flex-start;
    max-width:320px;animation:slideIn .3s ease;
  `;
  toast.innerHTML = `
    <div style="font-size:1.2rem">🔔</div>
    <div style="flex:1">
      <div style="font-weight:600;font-size:.875rem;margin-bottom:2px">${escHtml(title)}</div>
      <div style="font-size:.78rem;color:var(--text2)">${escHtml(body||"")}</div>
    </div>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;color:var(--text3);font-size:1rem">✕</button>
  `;
  const style = document.createElement("style");
  style.textContent = "@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}";
  document.head.appendChild(style);
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

// ── Utilities ─────────────────────────────────────────────────
function checkVerifyBanner(r) {
  const b = document.getElementById("verifyBanner");
  if (b && r.user && !r.user.email_verified) b.style.display = "flex";
}

function showAlert(el, msg, type = "error") {
  el.textContent = msg;
  el.className = "alert alert-" + type;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 5000);
}

function timeAgo(iso) {
  const str = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
  const d = Date.now() - new Date(str).getTime();
  const m = Math.floor(d/60000), h = Math.floor(m/60), dy = Math.floor(h/24);
  if (dy > 30) return new Date(str).toLocaleDateString();
  if (dy > 0)  return dy + "d ago";
  if (h  > 0)  return h  + "h ago";
  if (m  > 0)  return m  + "m ago";
  return "Just now";
}

function escHtml(t) {
  return String(t || "")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Skeleton loaders ──────────────────────────────────────────
function skeletonPost() {
  return `<div class="skeleton-card">
    <div style="display:flex;gap:12px;margin-bottom:14px">
      <div class="skeleton skeleton-avatar"></div>
      <div style="flex:1">
        <div class="skeleton skeleton-text w-40"></div>
        <div class="skeleton skeleton-text w-60"></div>
      </div>
    </div>
    <div class="skeleton skeleton-text w-80"></div>
    <div class="skeleton skeleton-text w-60"></div>
    <div class="skeleton skeleton-text w-40"></div>
  </div>`;
}

function skeletonCard() {
  return `<div class="skeleton-card">
    <div class="skeleton skeleton-text w-60"></div>
    <div class="skeleton skeleton-text w-40"></div>
    <div class="skeleton skeleton-text w-80"></div>
  </div>`;
}

// ── Infinite scroll ───────────────────────────────────────────
function setupInfiniteScroll(sentinel, callback) {
  if (!sentinel) return;
  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) callback();
  }, { threshold: 0.1 });
  observer.observe(sentinel);
  return observer;
}

// ── DOMContentLoaded ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    if (confirm("Sign out?")) API.logout();
  });
  document.getElementById("menuToggle")?.addEventListener("click", () => {
    document.getElementById("sidebar")?.classList.toggle("open");
  });
  document.getElementById("resendVerifyBtn")?.addEventListener("click", async () => {
    try {
      const r = await API.post("/auth/resend-verification");
      alert(r.dev_verify_url ? "DEV — Verify link:\n" + r.dev_verify_url : "Verification email sent!");
    } catch(e) { alert(e.message); }
  });
  const path = window.location.pathname.replace(/^\//, "").split("/")[0] || "feed";
  document.querySelector("[data-page='" + path + "']")?.classList.add("active");
  if (window.location.search.includes("verified=1")) {
    const u = API.getUser() || {};
    u.email_verified = true;
    sessionStorage.setItem("user", JSON.stringify(u));
    history.replaceState({}, "", window.location.pathname);
    setTimeout(() => alert("✅ Email verified! Welcome to CareerIQ."), 300);
  }
});
