import { Link, useSearchParams } from "react-router-dom";
import PageShell, { Card, Note, StateMessage } from "../components/PageShell";
import Poster from "../components/Poster";
import SearchBox from "../components/SearchBox";
import { useApi } from "../hooks/useApi";
import { NA, crore, croreRange, formatDate } from "../lib/format";

/** One side of the duel: a search box, or the chosen film with a Change button. */
function Slot({ label, id, onPick, onClear }) {
  const { data: f, error } = useApi(id ? `/api/films/${encodeURIComponent(id)}` : null);
  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <p className="mb-2 text-xs uppercase text-muted">{label}</p>
      {!id ? (
        <SearchBox onSelect={(film) => onPick(film.id)} placeholder="Search a film…" />
      ) : error ? (
        <p className="text-sm text-muted">
          Film not found.{" "}
          <button className="text-gold underline" onClick={onClear}>Pick another</button>
        </p>
      ) : !f ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : (
        <div className="flex items-center gap-3">
          <Poster src={f.poster_url} title={f.title} className="h-20 w-14 shrink-0 rounded" />
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium text-white">{f.title}</p>
            <p className="text-xs text-muted">{f.language}</p>
          </div>
          <button onClick={onClear} className="rounded-full border border-line px-3 py-1 text-xs text-muted hover:text-white">
            Change
          </button>
        </div>
      )}
    </div>
  );
}

function FigCell({ fig, widthPct }) {
  if (fig.amount_cr == null) return <span className="text-muted">{NA}</span>;
  return (
    <div>
      <p className="font-semibold text-gold-soft">{croreRange(fig.amount_cr, fig.amount_max_cr)}</p>
      {widthPct != null && (
        <div aria-hidden className="mt-1 h-2 rounded bg-panel-2">
          <div className="h-2 rounded bg-gold" style={{ width: `${widthPct}%` }} />
        </div>
      )}
      <p className="mt-1 text-xs text-muted">
        <span className="text-gold">{fig.label}</span>
        {fig.source_url && (
          <> · <a className="underline hover:text-white" href={fig.source_url} target="_blank" rel="noopener noreferrer">{fig.source_name ?? "source"}</a></>
        )}
      </p>
    </div>
  );
}

/** One table row. If `highlight` is set, the higher number gets a star. */
function Row({ label, a, b, numA, numB, highlight = false }) {
  const both = highlight && numA != null && numB != null && numA !== numB;
  const aWins = both && numA > numB;
  const bWins = both && numB > numA;
  const star = (
    <>
      <span aria-hidden className="ml-2 text-gold">★</span>
      <span className="sr-only"> (higher)</span>
    </>
  );
  return (
    <tr className="border-t border-line align-top">
      <th scope="row" className="w-28 px-3 py-3 text-left text-sm font-normal text-muted">{label}</th>
      <td className={`px-3 py-3 ${aWins ? "bg-gold/10" : ""}`}>{a}{aWins && star}</td>
      <td className={`px-3 py-3 ${bWins ? "bg-gold/10" : ""}`}>{b}{bWins && star}</td>
    </tr>
  );
}

const rating = (c, src) => c.ratings.find((r) => r.source === src)?.score ?? null;
const ratingText = (v) => (v == null ? NA : `${v.toFixed(1)} / 10`);
const roiText = (c) =>
  c.roi == null ? NA : c.roi_min != null ? `${c.roi.toFixed(1)}× (to ${c.roi_min.toFixed(1)}×)` : `${c.roi.toFixed(1)}×`;
const pct = (v, max) => (v != null && max ? Math.max(4, (v / max) * 100) : null);

function Comparison({ A, B }) {
  const maxBudget = Math.max(A.budget.amount_cr ?? 0, B.budget.amount_cr ?? 0);
  const maxWorld = Math.max(A.worldwide.amount_cr ?? 0, B.worldwide.amount_cr ?? 0);
  const showImdb = rating(A, "imdb") != null || rating(B, "imdb") != null;

  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-sm">
          <caption className="sr-only">Side-by-side comparison of {A.title} and {B.title}</caption>
          <thead>
            <tr>
              <td />
              {[A, B].map((c) => (
                <th key={c.id} scope="col" className="px-3 py-2 align-bottom">
                  <Link to={`/film/${c.id}`} className="block hover:text-gold">
                    <Poster src={c.poster_url} title={c.title} className="mb-2 h-40 w-28 rounded-lg" />
                    <span className="font-display text-lg text-white">{c.title}</span>
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <Row label="Language" a={A.language} b={B.language} />
            <Row label="Release" a={formatDate(A.release_date)} b={formatDate(B.release_date)} />
            <Row label="Director" a={A.director ?? NA} b={B.director ?? NA} />
            <Row label="Budget"
                 a={<FigCell fig={A.budget} widthPct={pct(A.budget.amount_cr, maxBudget)} />}
                 b={<FigCell fig={B.budget} widthPct={pct(B.budget.amount_cr, maxBudget)} />} />
            <Row label="Worldwide gross" highlight numA={A.worldwide.amount_cr} numB={B.worldwide.amount_cr}
                 a={<FigCell fig={A.worldwide} widthPct={pct(A.worldwide.amount_cr, maxWorld)} />}
                 b={<FigCell fig={B.worldwide} widthPct={pct(B.worldwide.amount_cr, maxWorld)} />} />
            <Row label="ROI" highlight numA={A.roi} numB={B.roi} a={roiText(A)} b={roiText(B)} />
            <Row label="TMDB rating" highlight numA={rating(A, "tmdb")} numB={rating(B, "tmdb")}
                 a={ratingText(rating(A, "tmdb"))} b={ratingText(rating(B, "tmdb"))} />
            {showImdb && (
              <Row label="IMDb rating" highlight numA={rating(A, "imdb")} numB={rating(B, "imdb")}
                   a={ratingText(rating(A, "imdb"))} b={ratingText(rating(B, "imdb"))} />
            )}
          </tbody>
        </table>
      </div>
      <Note>
        ★ marks the higher value where both films have one. Budget is not starred because a bigger budget
        is not "better". Bars compare the low end of reported budgets. ROI = worldwide gross ÷ budget. A
        figure shown as "Not available" is missing from the sources, not zero.
      </Note>
    </Card>
  );
}

export default function Duel() {
  const [params, setParams] = useSearchParams();
  const a = params.get("a");
  const b = params.get("b");
  const both = a && b;

  const { data, error, loading } = useApi(
    both ? `/api/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}` : null
  );

  function setSlot(key, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  }

  return (
    <PageShell title="Duel mode" subtitle="Pick two films and compare them side by side.">
      <div className="grid gap-4 md:grid-cols-2">
        <Slot label="Film A" id={a} onPick={(v) => setSlot("a", v)} onClear={() => setSlot("a", null)} />
        <Slot label="Film B" id={b} onPick={(v) => setSlot("b", v)} onClear={() => setSlot("b", null)} />
      </div>

      {!both && <p className="text-muted">Choose both films to see the comparison.</p>}
      {both && loading && <StateMessage loading />}
      {both && error && (error.status === 400 || error.status === 404 || error.status === 422 ? (
        <p role="alert" className="rounded-lg border border-line bg-panel p-4 text-muted">
          {error.status === 400 ? "Pick two different films." : "One of the films could not be found. Change it above."}
        </p>
      ) : (
        <StateMessage error={error} />
      ))}
      {both && data && <Comparison A={data.a} B={data.b} />}
    </PageShell>
  );
}