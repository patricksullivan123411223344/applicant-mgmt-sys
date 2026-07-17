import { API_BASE } from "./config.js";

let _configPromise = null;
let _clientPromise = null;

export async function fetchPublicConfig() {
  if (!_configPromise) {
    _configPromise = fetch(`${API_BASE}/api/v1/public-config`).then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load public config (${response.status})`);
      }
      return response.json();
    });
  }
  return _configPromise;
}

export async function getSupabaseClient() {
  if (_clientPromise) {
    return _clientPromise;
  }
  _clientPromise = (async () => {
    const config = await fetchPublicConfig();
    if (config.auth_disabled) {
      return null;
    }
    if (!config.supabase_url || !config.supabase_anon_key) {
      throw new Error(
        "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY on the server.",
      );
    }
    const { createClient } = await import("https://esm.sh/@supabase/supabase-js@2.49.1");
    return createClient(config.supabase_url, config.supabase_anon_key, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  })();
  return _clientPromise;
}
