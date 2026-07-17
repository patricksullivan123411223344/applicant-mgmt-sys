import {
  getSession,
  isAuthDisabled,
  isLikelyMissingAccountError,
  signInWithPassword,
  signUpWithPassword,
} from "./auth.js";

const form = document.getElementById("login-form");
const emailInput = document.getElementById("login-email");
const passwordInput = document.getElementById("login-password");
const button = document.getElementById("login-button");
const messageEl = document.getElementById("login-message");
const infoEl = document.getElementById("login-info");
const titleEl = document.getElementById("auth-title");
const taglineEl = document.getElementById("auth-tagline");
const toggleBtn = document.getElementById("auth-mode-toggle");

let mode = "signin";

function nextPath() {
  const params = new URLSearchParams(window.location.search);
  const next = params.get("next") || "/";
  if (!next.startsWith("/") || next.startsWith("//")) {
    return "/";
  }
  return next;
}

function showError(text) {
  infoEl.hidden = true;
  messageEl.hidden = false;
  messageEl.textContent = text;
}

function showInfo(text) {
  messageEl.hidden = true;
  infoEl.hidden = false;
  infoEl.textContent = text;
}

function clearMessages() {
  messageEl.hidden = true;
  infoEl.hidden = true;
}

function setMode(nextMode, { replaceUrl = true } = {}) {
  mode = nextMode === "signup" ? "signup" : "signin";
  const isSignup = mode === "signup";

  document.title = isSignup ? "Sign up — Housing Processor" : "Sign in — Housing Processor";
  titleEl.textContent = isSignup ? "Create an account" : "Staff sign in";
  taglineEl.textContent = isSignup
    ? "Create an account with email and password. You can sign in afterward on any page."
    : "Sign in with your email and password to use the operations API.";
  button.textContent = isSignup ? "Sign up" : "Sign in";
  passwordInput.autocomplete = isSignup ? "new-password" : "current-password";
  toggleBtn.textContent = isSignup
    ? "Already have an account? Sign in"
    : "Need an account? Sign up";

  if (replaceUrl) {
    const url = new URL(window.location.href);
    if (isSignup) {
      url.searchParams.set("mode", "signup");
    } else {
      url.searchParams.delete("mode");
    }
    window.history.replaceState({}, "", url);
  }
}

async function bootstrap() {
  try {
    if (await isAuthDisabled()) {
      window.location.replace("/");
      return;
    }
    const params = new URLSearchParams(window.location.search);
    setMode(params.get("mode") === "signup" ? "signup" : "signin", { replaceUrl: false });

    const session = await getSession();
    if (session) {
      window.location.replace(nextPath());
    }
  } catch (err) {
    showError(err?.message || String(err));
  }
}

toggleBtn?.addEventListener("click", () => {
  clearMessages();
  setMode(mode === "signup" ? "signin" : "signup");
});

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessages();
  button.disabled = true;
  const email = emailInput.value.trim();
  const password = passwordInput.value;

  try {
    if (mode === "signup") {
      const data = await signUpWithPassword(email, password);
      if (data.session) {
        window.location.replace(nextPath());
        return;
      }
      showInfo("Account created. Check your email to confirm, then sign in.");
      setMode("signin");
      button.disabled = false;
      return;
    }

    await signInWithPassword(email, password);
    window.location.replace(nextPath());
  } catch (err) {
    if (mode === "signin" && isLikelyMissingAccountError(err)) {
      setMode("signup");
      showError("No account found for that email. Create one below, or fix the email and try again.");
    } else {
      showError(err?.message || String(err));
    }
    button.disabled = false;
  }
});

void bootstrap();
