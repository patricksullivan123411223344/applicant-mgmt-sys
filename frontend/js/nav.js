import { getCurrentUserEmail, isAuthDisabled, loginUrl, signOut } from "./auth.js";

/**
 * Injects CRM navbar + group-number search into #site-nav.
 */
export async function mountNav(activePage = "") {
  const host = document.getElementById("site-nav");
  if (!host) {
    return;
  }

  const links = [
    { href: "/", id: "dashboard", label: "Dashboard" },
    { href: "/groups.html", id: "groups", label: "Groups" },
    { href: "/applications.html", id: "applications", label: "Applications" },
  ];

  const authDisabled = await isAuthDisabled();
  let email = "";
  try {
    email = (await getCurrentUserEmail()) || "";
  } catch {
    email = "";
  }

  const next = `${window.location.pathname}${window.location.search}`;
  // AUTH_DISABLED shows local-dev without login CTAs. No session → Log in / Sign up.
  const showAuthCtas = !authDisabled && !email;

  const userBlock = showAuthCtas
    ? `
      <div class="crm-user crm-auth-ctas">
        <a class="crm-auth-link" href="${loginUrl({ mode: "signin", next })}">Log in</a>
        <a class="crm-auth-link crm-auth-link-primary" href="${loginUrl({ mode: "signup", next })}">Sign up</a>
      </div>
    `
    : `
      <div class="crm-user">
        ${email ? `<span class="crm-user-email" title="${email}">${email}</span>` : ""}
        ${authDisabled ? "" : `<button type="button" class="crm-logout" id="nav-logout">Log out</button>`}
      </div>
    `;

  host.innerHTML = `
    <div class="crm-nav">
      <a class="crm-brand" href="/">Housing Processor</a>
      <nav class="crm-links" aria-label="Primary">
        ${links
          .map(
            (l) =>
              `<a href="${l.href}" class="${l.id === activePage ? "active" : ""}">${l.label}</a>`,
          )
          .join("")}
      </nav>
      <form class="crm-search" id="nav-group-search" action="/groups.html" method="get">
        <label class="visually-hidden" for="nav-group-number">Group number</label>
        <input
          id="nav-group-number"
          name="number"
          type="number"
          min="1"
          step="1"
          placeholder="Group #"
          inputmode="numeric"
        />
        <button type="submit">Go</button>
      </form>
      ${userBlock}
    </div>
  `;

  const form = document.getElementById("nav-group-search");
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = document.getElementById("nav-group-number");
    const value = (input?.value || "").trim();
    if (!value) {
      window.location.href = "/groups.html";
      return;
    }
    window.location.href = `/group.html?number=${encodeURIComponent(value)}`;
  });

  document.getElementById("nav-logout")?.addEventListener("click", () => {
    void signOut();
  });
}
