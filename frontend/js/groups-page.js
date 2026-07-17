import { listGroups } from "./api.js";
import { mountNav } from "./nav.js";

mountNav("groups");

const tbody = document.getElementById("groups-body");
const emptyEl = document.getElementById("groups-empty");
const errorEl = document.getElementById("groups-error");
const metaEl = document.getElementById("groups-meta");
const filterForm = document.getElementById("groups-filter");
const filterInput = document.getElementById("filter-group-number");

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

async function loadGroups(groupNumber) {
  errorEl.hidden = true;
  emptyEl.hidden = true;
  tbody.innerHTML = "";
  metaEl.textContent = "Loading…";

  try {
    const params = { limit: 100, offset: 0 };
    if (groupNumber) {
      params.groupNumber = Number(groupNumber);
    }
    const data = await listGroups(params);
    const items = data.items || [];
    metaEl.textContent = `${data.page?.total ?? items.length} group(s)`;

    if (!items.length) {
      emptyEl.hidden = false;
      emptyEl.textContent = groupNumber
        ? `No group found with number ${groupNumber}.`
        : "No groups yet — upload applications and assign groups in a later step.";
      return;
    }

    for (const g of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${g.group_number}</strong></td>
        <td>${g.status}</td>
        <td>${g.member_count}</td>
        <td>${formatDate(g.first_application_received_at)}</td>
        <td><a href="/group.html?number=${g.group_number}">Open</a></td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    errorEl.hidden = false;
    errorEl.textContent = err.message || String(err);
    metaEl.textContent = "";
  }
}

filterForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = (filterInput?.value || "").trim();
  const url = new URL(window.location.href);
  if (value) {
    url.searchParams.set("number", value);
  } else {
    url.searchParams.delete("number");
  }
  window.history.replaceState({}, "", url);
  loadGroups(value || undefined);
});

const initial = new URLSearchParams(window.location.search).get("number");
if (initial && filterInput) {
  filterInput.value = initial;
}
loadGroups(initial || undefined);
