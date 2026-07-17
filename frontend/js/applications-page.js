import { listApplications } from "./api.js";
import { mountNav } from "./nav.js";

mountNav("applications");

const tbody = document.getElementById("apps-body");
const emptyEl = document.getElementById("apps-empty");
const errorEl = document.getElementById("apps-error");
const metaEl = document.getElementById("apps-meta");

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

async function load() {
  metaEl.textContent = "Loading…";
  try {
    const data = await listApplications({ limit: 100, offset: 0 });
    const items = data.items || [];
    metaEl.textContent = `${data.page?.total ?? items.length} application(s)`;

    if (!items.length) {
      emptyEl.hidden = false;
      return;
    }

    for (const app of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="mono">${app.application_id}</td>
        <td>${app.original_filename}</td>
        <td>${app.status}${app.review_required ? " · review" : ""}</td>
        <td>${formatDate(app.received_at)}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    errorEl.hidden = false;
    errorEl.textContent = err.message || String(err);
    metaEl.textContent = "";
  }
}

load();
