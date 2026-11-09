import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Figure from "../components/Figure";
import Poster from "../components/Poster";
import CastCard from "../components/CastCard";
import { useApi } from "../hooks/useApi";
import { NA, crore, formatDate, runtime, year } from "../lib/format";

const MARKET_LABEL = {
  worldwide: "Worldwide", india_net: "India net", hindi_belt: "Hindi belt", overseas: "Overseas",
};
const SITE_LABEL = { bookmyshow: "BookMyShow", district: "District" };

/** Film backdrop that fades in behind the page once it has loaded. */
function Backdrop({ src }) {
  const [loaded, setLoaded] = useState(false);
  if (!src) return null;
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-0">
      <img
        src={src} alt="" onLoad={() => setLoaded(true)}
        className={`h-full w-full object-cover transition-opacity duration-[1500ms] ${loaded ? "opacity-40" : "opacity-0"}`}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-bg/30 via-bg/80 to-bg" />
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="font-display text-2xl text-white">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function Film() {
  const { id } = useParams();
  const { data: f, error, loading } = useApi(`/api/films/${id}`);

  useEffect(() => { window.scrollTo(0, 0); }, [id]);

  if (loading) return <p className="p-8 text-center text-muted">Loading…</p>;

  if (error) {
    return (
      <div role="alert" className="mx-auto max-w-lg p-8 text-center">
        <h1 className="font-display text-2xl text-white">
          {error.status === 404 ? "Film not found" : "Can't reach the API"}
        </h1>
        <p className="mt-2 text-muted">
          {error.status === 404
            ? "Try searching for another title."
            : "Start the backend with: uvicorn app.main:app --reload"}
        </p>
        <Link to="/" className="mt-4 inline-block text-gold underline">Back to home</Link>
      </div>
    );
  }

  const meta = [
    f.language,
    formatDate(f.release_date),
    runtime(f.runtime),
    f.director && `Directed by ${f.director}`,
  ].filter(Boolean);

  return (
    <div className="relative">
      <Backdrop key={f.backdrop_url} src={f.backdrop_url} />

      <div className="relative z-10 mx-auto max-w-6xl px-4 pb-16 pt-8">
        {/* Header */}
        <div className="grid gap-6 md:grid-cols-[16rem_1fr]">
          <Poster src={f.poster_url} title={f.title}
                  className="mx-auto aspect-[2/3] w-48 rounded-xl border border-line shadow-2xl md:w-full" />
          <div>
            {f.status === "upcoming" && (
              <span className="mb-2 inline-block rounded bg-gold px-2 py-0.5 text-xs font-bold text-black">
                UPCOMING
              </span>
            )}
            <h1 className="font-display text-4xl font-bold text-white sm:text-5xl">{f.title}</h1>
            <p className="mt-2 text-sm text-muted">{meta.join(" · ")}</p>
            {f.overview && <p className="mt-4 max-w-2xl leading-relaxed text-[#d8d8e6]">{f.overview}</p>}

            <div className="mt-5 flex flex-wrap gap-3">
              {f.trailer_url && (
                <a href={f.trailer_url} target="_blank" rel="noopener noreferrer"
                   className="rounded-full bg-gold px-5 py-2 text-sm font-semibold text-black hover:bg-gold-soft">
                  ▶ Watch trailer
                </a>
              )}
              <Link to={`/duel?a=${f.id}`}
                    className="rounded-full border border-gold px-5 py-2 text-sm font-semibold text-gold hover:bg-gold/10">
                Compare with another film
              </Link>
              {f.links.filter((l) => l.url).map((l) => (
                <a key={l.site} href={l.url} target="_blank" rel="noopener noreferrer"
                   className="rounded-full border border-line px-5 py-2 text-sm text-muted hover:text-white">
                  Book / see ratings on {SITE_LABEL[l.site] ?? l.site}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Money */}
        <Section title="Budget and box office">
          <div className="grid gap-4 md:grid-cols-3">
            <Figure title="Budget" data={f.budget} />
            <Figure title="Worldwide gross" data={f.worldwide} />
            <div className="rounded-xl border border-line bg-panel p-4">
              <p className="text-sm text-muted">Return on investment (ROI)</p>
              {f.roi != null ? (
                <>
                  <p className="mt-1 text-2xl font-semibold text-gold-soft">{f.roi.toFixed(1)}×</p>
                  {f.roi_min != null && (
                    <p className="mt-1 text-xs text-muted">
                      Falls to {f.roi_min.toFixed(1)}× if the top of the budget range is used.
                    </p>
                  )}
                  <p className="mt-2 text-xs text-muted">
                    Worldwide gross ÷ budget. Calculated here from the two Reported figures;
                    gross is not the producer's profit.
                  </p>
                </>
              ) : (
                <p className="mt-1 text-xl text-muted">{NA}</p>
              )}
            </div>
          </div>

          {f.collections.length > 0 && (
            <div className="mt-4 overflow-x-auto rounded-xl border border-line">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">All reported collection figures for {f.title}</caption>
                <thead className="bg-panel-2 text-xs uppercase text-muted">
                  <tr>
                    <th scope="col" className="px-3 py-2">Market</th>
                    <th scope="col" className="px-3 py-2">Amount</th>
                    <th scope="col" className="px-3 py-2">Source</th>
                    <th scope="col" className="px-3 py-2">Fetched</th>
                  </tr>
                </thead>
                <tbody>
                  {f.collections.map((c, i) => (
                    <tr key={i} className="border-t border-line">
                      <td className="px-3 py-2">{MARKET_LABEL[c.market] ?? c.market}</td>
                      <td className="px-3 py-2">{crore(c.amount_cr)} <span className="text-xs text-gold">{c.label}</span></td>
                      <td className="px-3 py-2">
                        <a className="underline hover:text-white" href={c.source_url}
                           target="_blank" rel="noopener noreferrer">{c.source_name}</a>
                      </td>
                      <td className="px-3 py-2 text-muted">{formatDate(c.fetched_on)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* Ratings */}
        <Section title="Ratings">
          {f.ratings.length > 0 ? (
            <div className="flex flex-wrap gap-4">
              {f.ratings.map((r) => (
                <div key={r.source} className="rounded-xl border border-line bg-panel px-5 py-3">
                  <p className="text-xs uppercase text-muted">{r.source === "tmdb" ? "TMDB" : "IMDb"}</p>
                  <p className="text-2xl font-semibold text-gold-soft">
                    {r.score.toFixed(1)}<span className="text-sm text-muted"> / 10</span>
                  </p>
                  {r.vote_count != null && (
                    <p className="text-xs text-muted">{r.vote_count.toLocaleString("en-IN")} votes</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">{NA}</p>
          )}
        </Section>

        {/* Cast and crew */}
        {f.crew.length > 0 && (
          <Section title="Cast and crew">
            <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6">
              {f.crew.map((p) => (
                <li key={`${p.person_id}-${p.role}`}><CastCard person={p} /></li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-muted">
              Hero, heroine and villain labels come from TMDB billing order plus manual corrections.
            </p>
          </Section>
        )}

        {/* Similar */}
        {f.similar.length > 0 && (
          <Section title="Similar films">
            <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-6">
              {f.similar.map((s) => (
                <li key={s.id}>
                  <Link to={`/film/${s.id}`} className="group block">
                    <Poster src={s.poster_url} title={s.title}
                            className="aspect-[2/3] w-full rounded-lg border border-line transition group-hover:border-gold" />
                    <p className="mt-2 truncate text-sm font-medium text-white">{s.title}</p>
                    <p className="text-xs text-muted">{year(s.release_date)} · {s.reason}</p>
                  </Link>
                </li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </div>
  );
}