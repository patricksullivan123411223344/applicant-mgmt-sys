import { API_BASE } from "./config.js";
import { getAccessToken, loginUrl, refreshSession } from "./auth.js";

export class ApiError extends Error {
  constructor(message, status, { hadToken = false } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.hadToken = hadToken;
  }
}

export function isUnauthorizedError(err) {
  return err?.status === 401;
}

export function isForbiddenError(err) {
  return err?.status === 403;
}

export function authRequiredMessage(prefix = "Sign in to view this data.") {
  return `${prefix} Use Log in in the navbar, or open ${loginUrl()}.`;
}

export function formatApiAuthError(err, prefix = "Sign in to view this data.") {
  if (isUnauthorizedError(err) && !err.hadToken) {
    return authRequiredMessage(prefix);
  }
  if (isUnauthorizedError(err) || isForbiddenError(err)) {
    return err.message || "Your session was rejected by the API. Try signing out and back in.";
  }
  return err?.message || String(err);
}

async function parseError(response) {
  try {
    const body = await response.json();
    if (body?.errors?.length) {
      return body.errors.map((e) => e.message || e.code).join("; ");
    }
    if (body?.detail) {
      return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    }
    return JSON.stringify(body);
  } catch {
    return response.statusText || `HTTP ${response.status}`;
  }
}

async function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = await getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return { headers, hadToken: Boolean(token) };
}

async function requestJson(path, { auth = true, method = "GET", body, retry = true } = {}) {
  let hadToken = false;
  let headers = {};
  if (auth) {
    const authResult = await authHeaders();
    headers = authResult.headers;
    hadToken = authResult.hadToken;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body,
  });

  if (response.status === 401 && auth && hadToken && retry) {
    try {
      await refreshSession();
    } catch {
      throw new ApiError(await parseError(response), 401, { hadToken: true });
    }
    return requestJson(path, { auth, method, body, retry: false });
  }

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status, { hadToken });
  }
  return response.json();
}

export function fetchLive() {
  return requestJson("/health/live", { auth: false });
}

export function fetchReady() {
  return requestJson("/health/ready", { auth: false });
}

export function fetchVersion() {
  return requestJson("/api/v1/system/version");
}

export async function uploadApplication(file) {
  const form = new FormData();
  form.append("file", file);
  form.append("source", "manual_upload");

  let hadToken = false;
  const attempt = async (retry) => {
    const authResult = await authHeaders();
    hadToken = authResult.hadToken;
    const response = await fetch(`${API_BASE}/api/v1/applications`, {
      method: "POST",
      headers: authResult.headers,
      body: form,
    });
    if (response.status === 401 && hadToken && retry) {
      try {
        await refreshSession();
      } catch {
        throw new ApiError(await parseError(response), 401, { hadToken: true });
      }
      return attempt(false);
    }
    if (!response.ok) {
      throw new ApiError(await parseError(response), response.status, { hadToken });
    }
    return response.json();
  };

  return attempt(true);
}

export async function listApplications({ limit = 50, offset = 0, status } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (status) {
    params.set("status_filter", status);
  }
  return requestJson(`/api/v1/applications?${params}`);
}

export async function listGroups({ limit = 50, offset = 0, groupNumber, status } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (groupNumber != null && groupNumber !== "") {
    params.set("group_number", String(groupNumber));
  }
  if (status) {
    params.set("status_filter", status);
  }
  return requestJson(`/api/v1/groups?${params}`);
}

export function getGroup(groupId) {
  return requestJson(`/api/v1/groups/${groupId}`);
}

export function getGroupByNumber(groupNumber) {
  return requestJson(`/api/v1/groups/by-number/${groupNumber}`);
}
