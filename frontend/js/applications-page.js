import { listApplications, formatApiAuthError } from "./api.js";
import { mountNav } from "./nav.js";

await mountNav("applications");
initApplicationsPage();

function initApplicationsPage() {
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
          <td class="mono"><a href="/application.html?id=${app.application_id}">${app.application_id}</a></td>
          <td>${app.original_filename}</td>
          <td>${app.status}${app.review_required ? " · review" : ""}</td>
          <td>${formatDate(app.received_at)}</td>
        `;
        tbody.appendChild(tr);
      }
    } catch (err) {
      errorEl.hidden = false;
      errorEl.textContent = formatApiAuthError(err, "Sign in to view applications.");
      metaEl.textContent = "";
    }
  }

  load();
}
