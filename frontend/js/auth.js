import { fetchPublicConfig, getSupabaseClient } from "./supabase-client.js";

const LOGIN_PATH = "/login.html";

export async function isAuthDisabled() {
  const config = await fetchPublicConfig();
  return Boolean(config.auth_disabled);
}

export async function getSession() {
  if (await isAuthDisabled()) {
    return null;
  }
  const client = await getSupabaseClient();
  if (!client) {
    return null;
  }
  const { data, error } = await client.auth.getSession();
  if (error) {
    throw error;
  }
  return data.session;
}

export async function refreshSession() {
  if (await isAuthDisabled()) {
    return null;
  }
  const client = await getSupabaseClient();
  if (!client) {
    return null;
  }
  const { data, error } = await client.auth.refreshSession();
  if (error) {
    throw error;
  }
  return data.session;
}

export async function getAccessToken() {
  if (await isAuthDisabled()) {
    return null;
  }
  let session = await getSession();
  if (!session?.access_token) {
    try {
      session = await refreshSession();
    } catch {
      return null;
    }
  }
  return session?.access_token ?? null;
}

export async function getCurrentUserEmail() {
  if (await isAuthDisabled()) {
    return "local-dev";
  }
  const session = await getSession();
  return session?.user?.email ?? null;
}

/**
 * Soft session check — does not redirect. Pages stay browsable when logged out.
 */
export async function requireSession() {
  if (await isAuthDisabled()) {
    return { authDisabled: true, session: null };
  }
  const session = await getSession();
  return { authDisabled: false, session };
}

export async function signInWithPassword(email, password) {
  const client = await getSupabaseClient();
  if (!client) {
    throw new Error("Auth is disabled in this environment.");
  }
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) {
    throw error;
  }
  return data;
}

export async function signUpWithPassword(email, password) {
  const client = await getSupabaseClient();
  if (!client) {
    throw new Error("Auth is disabled in this environment.");
  }
  const { data, error } = await client.auth.signUp({ email, password });
  if (error) {
    throw error;
  }
  return data;
}

/**
 * True when sign-in failed because the email is not registered (steer to sign-up).
 * Wrong password for an existing user returns false.
 */
export function isLikelyMissingAccountError(error) {
  const message = String(error?.message || error || "").toLowerCase();
  const status = error?.status;
  if (message.includes("user not found") || message.includes("email not found")) {
    return true;
  }
  // Supabase often returns a generic invalid-credentials message for unknown emails.
  if (
    status === 400 &&
    (message.includes("invalid login credentials") || message.includes("invalid_credentials"))
  ) {
    return true;
  }
  return false;
}

export function loginUrl({ mode = "signin", next } = {}) {
  const params = new URLSearchParams();
  if (mode === "signup") {
    params.set("mode", "signup");
  }
  if (next) {
    params.set("next", next);
  }
  const qs = params.toString();
  return qs ? `${LOGIN_PATH}?${qs}` : LOGIN_PATH;
}

export async function signOut() {
  if (await isAuthDisabled()) {
    window.location.href = "/";
    return;
  }
  const client = await getSupabaseClient();
  if (client) {
    const { error } = await client.auth.signOut();
    if (error) {
      throw error;
    }
  }
  window.location.href = "/";
}
