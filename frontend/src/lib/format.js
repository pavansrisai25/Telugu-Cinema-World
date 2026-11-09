export const NA = "Not available";
const nf = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });

export const crore = (n) => (n == null ? NA : `₹${nf.format(n)} crore`);

/** "₹1,000–1,400 crore" for a reported range, else a single figure. */
export function croreRange(min, max) {
  if (min == null) return NA;
  if (max == null || max === min) return crore(min);
  return `₹${nf.format(min)}–${nf.format(max)} crore`;
}

export function formatDate(iso) {
  if (!iso) return NA;
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
  });
}

export const year = (iso) => (iso ? iso.slice(0, 4) : "");

export function runtime(min) {
  if (!min) return null;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}