import { useEffect, useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { year } from "../lib/format";
import Poster from "./Poster";

export default function SearchBox({
  large = false,
  onSelect,
  placeholder = "Search a film, e.g. Baahubali, RRR, Varanasi",
}) {
  const navigate = useNavigate();
  const listId = useId();
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);

  // Wait 200 ms after typing stops, then search. Cancel the old request.
  useEffect(() => {
    const term = q.trim();
    if (!term) {
      setResults([]);
      setStatus("idle");
      return;
    }
    setStatus("loading");
    const ctrl = new AbortController();
    const timer = setTimeout(() => {
      api(`/api/search?q=${encodeURIComponent(term)}&limit=8`, { signal: ctrl.signal })
        .then((data) => { setResults(data); setStatus("done"); setActive(-1); })
        .catch((err) => { if (err.name !== "AbortError") setStatus("error"); });
    }, 200);
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, [q]);

  function go(film) {
    if (onSelect) onSelect(film);
    else navigate(`/film/${film.id}`);
    setOpen(false);
    setQ("");
  }

  function onKeyDown(e) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      const pick = results[active] ?? results[0];
      if (pick) { e.preventDefault(); go(pick); }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  const showPanel = open && q.trim() !== "";

  return (
    <div className="relative w-full">
      <label htmlFor={`${listId}-input`} className="sr-only">Search films</label>
      <input
        id={`${listId}-input`}
        type="search"
        role="combobox"
        aria-expanded={showPanel && results.length > 0}
        aria-controls={`${listId}-list`}
        aria-activedescendant={active >= 0 ? `${listId}-opt-${active}` : undefined}
        aria-autocomplete="list"
        autoComplete="off"
        placeholder="Search a film, e.g. Baahubali, RRR, Varanasi"
        value={q}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={onKeyDown}
        className={`w-full rounded-full border border-line bg-panel px-5 text-white placeholder:text-muted focus:border-gold ${
          large ? "py-4 text-lg" : "py-2 text-sm"
        }`}
      />

      {showPanel && (
        <div className="absolute left-0 right-0 top-full z-40 mt-2 overflow-hidden rounded-2xl border border-line bg-panel shadow-2xl">
          {results.length > 0 ? (
            <ul id={`${listId}-list`} role="listbox" aria-label="Matching films">
              {results.map((f, i) => (
                <li
                  key={f.id}
                  id={`${listId}-opt-${i}`}
                  role="option"
                  aria-selected={i === active}
                  // mousedown runs before blur, so the click is not lost
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => go(f)}
                  onMouseEnter={() => setActive(i)}
                  className={`flex cursor-pointer items-center gap-3 px-3 py-2 ${
                    i === active ? "bg-panel-2" : ""
                  }`}
                >
                  <Poster src={f.poster_url} title={f.title} className="h-14 w-10 shrink-0 rounded" />
                  <span>
                    <span className="block text-sm font-medium text-white">{f.title}</span>
                    <span className="block text-xs text-muted">
                      {year(f.release_date)} · {f.language}
                      {f.status === "upcoming" && " · Upcoming"}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p role="status" className="px-4 py-3 text-sm text-muted">
              {status === "loading" && "Searching…"}
              {status === "done" && "No films match. Try fewer letters."}
              {status === "error" && "Search is unavailable. Is the backend running?"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}