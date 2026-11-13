// Shared chart styling for the dark theme.
export const AXIS = { stroke: "#a7a7bb", tick: { fill: "#a7a7bb", fontSize: 12 } };
export const GRID = "#2b2b3a";
export const TOOLTIP = {
  contentStyle: { background: "#14141c", border: "1px solid #2b2b3a", borderRadius: 8, color: "#ececf4" },
  labelStyle: { color: "#f5b942" },
  itemStyle: { color: "#ececf4" },
};

const LANG = { Telugu: "#f5b942", Hindi: "#6aa9ff", Kannada: "#7ad9a3", Tamil: "#ff8a8a", Malayalam: "#c79bff" };
const FALLBACK = ["#ffa94d", "#74d7ec", "#e599f7", "#b2f2bb"];
export const langColor = (lang, i = 0) => LANG[lang] ?? FALLBACK[i % FALLBACK.length];