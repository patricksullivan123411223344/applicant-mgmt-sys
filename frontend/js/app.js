import {
  fetchLive,
  fetchReady,
  fetchVersion,
  uploadApplication,
  isUnauthorizedError,
  formatApiAuthError,
} from "./api.js";
import { mountNav } from "./nav.js";

await mountNav("dashboard");
initDashboard();

function initDashboard() {
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
      const [live, ready] = await Promise.all([fetchLive(), fetchReady()]);
      setPill(liveEl, live.status === "ok", live.status || "ok");
      const readyOk = ready.status === "ready";
      setPill(
        readyEl,
        readyOk,
        readyOk ? "ready" : ready.reason || ready.status || "not_ready",
      );

      try {
        const version = await fetchVersion();
        versionEl.textContent = version.version || "—";
      } catch (err) {
        if (isUnauthorizedError(err) || err?.status === 403) {
          versionEl.textContent = err.hadToken ? "session rejected" : "sign in required";
        } else {
          throw err;
        }
      }
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
      showUploadMessage(formatApiAuthError(err, "Sign in to upload applications."), {
        error: true,
      });
    } finally {
      uploadButton.disabled = false;
    }
  });

  void refreshStatus();
}
