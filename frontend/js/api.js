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
  if (body != null && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body != null && !(body instanceof FormData) ? JSON.stringify(body) : body,
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
  if (response.status === 204) {
    return null;
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
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

export function getApplication(applicationId) {
  return requestJson(`/api/v1/applications/${applicationId}`);
}

export function reprocessApplication(applicationId, reason = "manual_reprocess") {
  return requestJson(`/api/v1/applications/${applicationId}/reprocess`, {
    method: "POST",
    body: {
      expected_version: 1,
      reason,
    },
  });
}

export function upsertApplicant(applicationId, payload) {
  return requestJson(`/api/v1/applications/${applicationId}/applicant`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteApplicant(applicantId) {
  return requestJson(`/api/v1/applicants/${applicantId}`, { method: "DELETE" });
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

export function createGroup(payload) {
  return requestJson(`/api/v1/groups`, { method: "POST", body: payload });
}

export function addGroupMember(groupId, payload) {
  return requestJson(`/api/v1/groups/${groupId}/members`, { method: "POST", body: payload });
}

export function setGroupContact(groupId, payload) {
  return requestJson(`/api/v1/groups/${groupId}/contact`, { method: "PUT", body: payload });
}

export function createExcelExport() {
  return requestJson(`/api/v1/exports/excel`, {
    method: "POST",
    body: {},
  });
}

export function exportDownloadUrl(exportId) {
  return `${API_BASE}/api/v1/exports/${exportId}/download`;
}
