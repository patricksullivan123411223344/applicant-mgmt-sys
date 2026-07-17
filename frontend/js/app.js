import {
  fetchLive,
  fetchReady,
  fetchVersion,
  uploadApplication,
} from "./api.js";
import { mountNav } from "./nav.js";

mountNav("dashboard");

const liveEl = document.getElementById("status-live");
const readyEl = document.getElementById("status-ready");
const versionEl = document.getElementById("status-version");
const statusErrorEl = document.getElementById("status-error");
const form = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadButton = document.getElementById("upload-button");
const uploadMessage = document.getElementById("upload-message");
const uploadResult = document.getElementById("upload-result");

function setPill(el, ok, label) {
  el.textContent = label;
  el.classList.remove("ok", "bad", "pending");
  el.classList.add(ok ? "ok" : "bad");
}

async function refreshStatus() {
  statusErrorEl.hidden = true;
  try {
    const [live, ready, version] = await Promise.all([
      fetchLive(),
      fetchReady(),
      fetchVersion(),
    ]);
    setPill(liveEl, live.status === "ok", live.status || "ok");
    const readyOk = ready.status === "ready";
    setPill(
      readyEl,
      readyOk,
      readyOk ? "ready" : ready.reason || ready.status || "not_ready",
    );
    versionEl.textContent = version.version || "—";
  } catch (err) {
    setPill(liveEl, false, "error");
    setPill(readyEl, false, "error");
    versionEl.textContent = "—";
    statusErrorEl.hidden = false;
    statusErrorEl.textContent = err.message || String(err);
  }
}

function showUploadMessage(text, { error = false } = {}) {
  uploadMessage.hidden = false;
  uploadMessage.textContent = text;
  uploadMessage.classList.toggle("error", error);
  uploadMessage.classList.toggle("success", !error);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files?.[0];
  if (!file) {
    showUploadMessage("Choose a .docx file first.", { error: true });
    return;
  }

  uploadButton.disabled = true;
  uploadResult.hidden = true;
  showUploadMessage("Uploading…");

  try {
    const result = await uploadApplication(file);
    showUploadMessage(
      result.status === "duplicate"
        ? "Duplicate file detected — existing application returned."
        : "Application accepted.",
    );
    uploadResult.hidden = false;
    uploadResult.textContent = JSON.stringify(result, null, 2);
    fileInput.value = "";
  } catch (err) {
    showUploadMessage(err.message || String(err), { error: true });
  } finally {
    uploadButton.disabled = false;
  }
});

refreshStatus();
