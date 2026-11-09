// In development the Vite proxy handles /api. In production set VITE_API_URL.
const BASE = import.meta.env.VITE_API_URL ?? "";

export async function api(path, { signal } = {}) {
  const res = await fetch(`${BASE}${path}`, { signal });
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}