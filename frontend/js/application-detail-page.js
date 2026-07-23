import {
  getApplication,
  reprocessApplication,
  upsertApplicant,
  deleteApplicant,
  createGroup,
  getGroupByNumber,
  addGroupMember,
  formatApiAuthError,
} from "./api.js";
import { mountNav } from "./nav.js";

await mountNav("applications");

const params = new URLSearchParams(window.location.search);
const applicationId = params.get("id");
const titleEl = document.getElementById("app-title");
const metaEl = document.getElementById("app-meta");
const errorEl = document.getElementById("app-error");
const messageEl = document.getElementById("app-message");
const warningsEl = document.getElementById("app-warnings");
const groupStatusEl = document.getElementById("group-status");
const pendingEl = document.getElementById("pending-roommates");
const extractedContactEl = document.getElementById("extracted-contact");
const extractedRoommatesEl = document.getElementById("extracted-roommates");
const extractedChoicesEl = document.getElementById("extracted-choices");
const processButton = document.getElementById("process-button");
const createGroupButton = document.getElementById("create-group-button");
const deleteApplicantButton = document.getElementById("delete-applicant-button");
const form = document.getElementById("applicant-form");
const attachForm = document.getElementById("attach-form");

function showError(text) {
  messageEl.hidden = true;
  errorEl.hidden = false;
  errorEl.textContent = text;
}

function showMessage(text) {
  errorEl.hidden = true;
  messageEl.hidden = false;
  messageEl.textContent = text;
}

function filenameNameHint(filename) {
  if (!filename) return "";
  const match = filename.match(/^\d+-(.+?)-Student-App\.docx$/i);
  if (!match) return "";
  return match[1].replace(/[-_]+/g, " ").trim();
}

function displayValue(value) {
  if (value == null || value === "") return "";
  return String(value);
}

function fill(detail) {
  titleEl.textContent = detail.original_filename || "Application";
  metaEl.textContent = `${detail.status} · received ${detail.received_at || "—"} · v${detail.version}`;
  document.getElementById("app-version").value = String(detail.version);
  document.getElementById("applicant-id").value = detail.applicant_id || "";
  const name =
    detail.applicant_name ||
    filenameNameHint(detail.original_filename) ||
    "";
  document.getElementById("full-name").value = name;
  document.getElementById("email").value = displayValue(detail.applicant_email);
  document.getElementById("phone").value = displayValue(detail.applicant_phone);
  document.getElementById("gpa").value = displayValue(detail.applicant_gpa);

  const warnings = detail.warnings || [];
  const visibleWarnings = warnings.filter(
    (w) => !w.startsWith("extracted_v1:") && !w.startsWith("pending_roommates:")
  );
  warningsEl.textContent = visibleWarnings.join("\n") || "(none)";

  const roommates = detail.pending_roommates || [];
  pendingEl.textContent = roommates.length
    ? `Pending roommates: ${roommates.join(", ")}`
    : "";

  if (extractedContactEl) {
    extractedContactEl.textContent = detail.contact_person || "—";
  }
  if (extractedRoommatesEl) {
    extractedRoommatesEl.textContent = roommates.length ? roommates.join(", ") : "—";
  }
  if (extractedChoicesEl) {
    const choices = detail.property_choices || [];
    extractedChoicesEl.textContent = choices.length
      ? choices.map((c) => `${c.rank}: ${c.raw}`).join(" · ")
      : "—";
  }

  if (detail.group_id) {
    groupStatusEl.textContent = `Linked to group ${detail.group_id}`;
  } else {
    groupStatusEl.textContent = "Not in a group yet.";
  }
  createGroupButton.disabled = !detail.applicant_id;
  if (deleteApplicantButton) {
    deleteApplicantButton.hidden = !detail.applicant_id;
    deleteApplicantButton.disabled = Boolean(detail.group_id);
    deleteApplicantButton.title = detail.group_id
      ? "Remove this applicant from their group before deleting."
      : "Permanently delete this applicant record";
  }
}

async function reload() {
  if (!applicationId) {
    showError("Missing application id. Open a row from Applications.");
    return;
  }
  const detail = await getApplication(applicationId);
  fill(detail);
  return detail;
}

processButton?.addEventListener("click", async () => {
  processButton.disabled = true;
  try {
    const result = await reprocessApplication(applicationId);
    showMessage(`Processed → ${result.status}`);
    await reload();
  } catch (err) {
    showError(formatApiAuthError(err, "Sign in to process applications."));
  } finally {
    processButton.disabled = false;
  }
});

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = {
      expected_version: Number(document.getElementById("app-version").value || 1),
      full_name: document.getElementById("full-name").value.trim(),
      email: document.getElementById("email").value.trim() || null,
      phone: document.getElementById("phone").value.trim() || null,
      gpa: document.getElementById("gpa").value.trim() || null,
      applicant_id: document.getElementById("applicant-id").value || null,
      reason: "manual_correction",
    };
    await upsertApplicant(applicationId, payload);
    showMessage("Applicant saved.");
    await reload();
  } catch (err) {
    showError(formatApiAuthError(err, "Sign in to save applicant."));
  }
});

deleteApplicantButton?.addEventListener("click", async () => {
  const applicantId = document.getElementById("applicant-id").value;
  if (!applicantId) {
    showError("No applicant linked to this application.");
    return;
  }
  const confirmed = window.confirm(
    "Delete this applicant and their application permanently? They will be removed from Applications and cannot be undone."
  );
  if (!confirmed) {
    return;
  }
  deleteApplicantButton.disabled = true;
  try {
    await deleteApplicant(applicantId);
    window.location.href = "/applications.html";
  } catch (err) {
    showError(formatApiAuthError(err, "Sign in to delete applicant."));
    deleteApplicantButton.disabled = false;
  }
});

createGroupButton?.addEventListener("click", async () => {
  const applicantId = document.getElementById("applicant-id").value;
  if (!applicantId) {
    showError("Save or process an applicant first.");
    return;
  }
  createGroupButton.disabled = true;
  try {
    const group = await createGroup({
      applicant_id: applicantId,
      source_application_id: applicationId,
      make_contact: true,
      reason: "manual_create",
    });
    showMessage(`Created group #${group.group_number}`);
    window.location.href = `/group.html?number=${group.group_number}`;
  } catch (err) {
    showError(formatApiAuthError(err, "Sign in to create a group."));
    createGroupButton.disabled = false;
  }
});

attachForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const applicantId = document.getElementById("applicant-id").value;
  if (!applicantId) {
    showError("Save or process an applicant first.");
    return;
  }
  const groupNumber = Number(document.getElementById("attach-group-number").value);
  try {
    const group = await getGroupByNumber(groupNumber);
    await addGroupMember(group.group_id, {
      applicant_id: applicantId,
      source_application_id: applicationId,
      expected_group_version: group.version,
      reason: "manual_attach",
    });
    showMessage(`Attached to group #${groupNumber}`);
    window.location.href = `/group.html?number=${groupNumber}`;
  } catch (err) {
    showError(formatApiAuthError(err, "Sign in to attach to a group."));
  }
});

try {
  if (!applicationId) {
    showError("Missing application id.");
  } else {
    await reload();
  }
} catch (err) {
  showError(formatApiAuthError(err, "Sign in to view this application."));
}
