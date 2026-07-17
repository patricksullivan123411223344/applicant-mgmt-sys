import {
  getGroupByNumber,
  formatApiAuthError,
  isUnauthorizedError,
  isForbiddenError,
} from "./api.js";
import { mountNav } from "./nav.js";

await mountNav("groups");
initGroupDetailPage();

function initGroupDetailPage() {
  const titleEl = document.getElementById("group-title");
  const metaEl = document.getElementById("group-meta");
  const errorEl = document.getElementById("group-error");
  const emptyEl = document.getElementById("group-empty");
  const tbody = document.getElementById("members-body");

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  async function load() {
    const params = new URLSearchParams(window.location.search);
    const number = params.get("number");
    if (!number) {
      errorEl.hidden = false;
      errorEl.textContent = "Missing group number. Use the navbar search or Groups list.";
      return;
    }

    titleEl.textContent = `Group ${number}`;
    metaEl.textContent = "Loading…";

    try {
      const group = await getGroupByNumber(number);
      titleEl.textContent = `Group ${group.group_number}`;
      metaEl.textContent = `${group.status} · ${group.member_count} member(s) · first received ${formatDate(group.first_application_received_at)}`;

      const members = group.members || [];
      if (!members.length) {
        emptyEl.hidden = false;
        emptyEl.textContent = "This group has no members yet.";
        return;
      }

      for (const m of members) {
        const tr = document.createElement("tr");
        if (m.is_contact) {
          tr.classList.add("is-contact");
        }
        tr.innerHTML = `
          <td class="${m.is_contact ? "contact-name" : ""}">${m.full_name}</td>
          <td>${m.is_contact ? "Yes" : ""}</td>
          <td>${m.email || "—"}</td>
          <td>${m.phone || "—"}</td>
          <td>${formatDate(m.joined_at)}</td>
        `;
        tbody.appendChild(tr);
      }
    } catch (err) {
      errorEl.hidden = false;
      errorEl.textContent = formatApiAuthError(err, "Sign in to view this group.");
      metaEl.textContent = "";
      if (!isUnauthorizedError(err) && !isForbiddenError(err)) {
        emptyEl.hidden = false;
        emptyEl.textContent = `Group ${number} was not found.`;
      }
    }
  }

  load();
}
