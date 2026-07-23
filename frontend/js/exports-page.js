import { createExcelExport, exportDownloadUrl, formatApiAuthError } from "./api.js";
import { getAccessToken } from "./auth.js";
import { mountNav } from "./nav.js";

await mountNav("exports");

const button = document.getElementById("export-button");
const messageEl = document.getElementById("export-message");
const errorEl = document.getElementById("export-error");
const linkWrap = document.getElementById("export-link-wrap");
const link = document.getElementById("export-link");

button?.addEventListener("click", async () => {
  button.disabled = true;
  errorEl.hidden = true;
  messageEl.hidden = true;
  try {
    const result = await createExcelExport();
    const token = await getAccessToken();
    const url = exportDownloadUrl(result.export_id);
    messageEl.hidden = false;
    messageEl.className = "message success";
    messageEl.textContent = `Export ${result.status}: ${result.export_id}`;
    linkWrap.hidden = false;
    link.href = url;
    link.onclick = async (event) => {
      event.preventDefault();
      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error(`Download failed (${response.status})`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `housing-export-${result.export_id}.xlsx`;
      a.click();
      URL.revokeObjectURL(objectUrl);
    };
  } catch (err) {
    errorEl.hidden = false;
    errorEl.textContent = formatApiAuthError(err, "Sign in to export Excel.");
  } finally {
    button.disabled = false;
  }
});
