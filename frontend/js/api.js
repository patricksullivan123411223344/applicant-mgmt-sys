import { API_BASE } from "./config.js";

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

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export function fetchLive() {
  return getJson("/health/live");
}

export function fetchReady() {
  return getJson("/health/ready");
}

export function fetchVersion() {
  return getJson("/api/v1/system/version");
}

export async function uploadApplication(file) {
  const form = new FormData();
  form.append("file", file);
  form.append("source", "manual_upload");

  const response = await fetch(`${API_BASE}/api/v1/applications`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function listApplications({ limit = 50, offset = 0, status } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (status) {
    params.set("status_filter", status);
  }
  return getJson(`/api/v1/applications?${params}`);
}

export async function listGroups({ limit = 50, offset = 0, groupNumber, status } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (groupNumber != null && groupNumber !== "") {
    params.set("group_number", String(groupNumber));
  }
  if (status) {
    params.set("status_filter", status);
  }
  return getJson(`/api/v1/groups?${params}`);
}

export function getGroup(groupId) {
  return getJson(`/api/v1/groups/${groupId}`);
}

export function getGroupByNumber(groupNumber) {
  return getJson(`/api/v1/groups/by-number/${groupNumber}`);
}
