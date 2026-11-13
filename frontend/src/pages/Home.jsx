import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import SearchBox from "../components/SearchBox";
import Poster from "../components/Poster";
import { useApi } from "../hooks/useApi";
import { crore, year } from "../lib/format";

const STORY = [
  ["2015", "Baahubali: The Beginning"],
  ["2022", "RRR"],
  ["2024", "Pushpa 2 and Kalki 2898 AD"],
  ["7 Apr 2027", "Varanasi"],
];

export default function Home() {
  const { data, error, loading } = useApi("/api/analytics/overview");

  return (
    <div>
      <section className="relative overflow-hidden px-4 pb-16 pt-20 text-center">
        <div aria-hidden className="absolute inset-0 -z-0 bg-[radial-gradient(ellipse_at_top,rgba(245,185,66,0.18),transparent_60%)]" />
        <div className="relative z-10 mx-auto max-w-3xl">
          <motion.h1
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="font-display text-4xl font-bold leading-tight text-white sm:text-6xl"
          >
            Telugu cinema, <span className="text-gold">to the world</span>
          </motion.h1>
          <p className="mx-auto mt-4 max-w-xl text-muted">
            How a regional film industry became a pan-India and global force,
            told with public data. Every money figure shows its source.
          </p>
          <div className="mx-auto mt-8 max-w-xl"><SearchBox large /></div>

          <ol className="mt-10 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm">
            {STORY.map(([when, what]) => (
              <li key={when} className="text-muted">
                <span className="font-semibold text-gold">{when}</span> {what}
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <h2 className="font-display text-2xl text-white">Biggest grossers in this dataset</h2>
        <p className="mt-1 text-sm text-muted">
          Worldwide gross, <span className="text-gold">Reported</span>. Open a film to see the source.
          This is a curated sample of films, not the whole industry.
        </p>

        {loading && <p className="mt-6 text-muted">Loading…</p>}
        {error && (
          <p role="alert" className="mt-6 rounded-lg border border-line bg-panel p-4 text-muted">
            Can't reach the API. Start the backend:{" "}
            <code className="text-gold">uvicorn app.main:app --reload</code>
          </p>
        )}

        {data && (
          <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
            {data.top_grossers.map((f) => (
              <li key={f.id}>
                <Link to={`/film/${f.id}`} className="group block">
                  <Poster src={f.poster_url} title={f.title}
                          className="aspect-[2/3] w-full rounded-lg border border-line transition group-hover:border-gold" />
                  <p className="mt-2 truncate text-sm font-medium text-white">{f.title}</p>
                  <p className="text-xs text-muted">{year(f.release_date)} · {crore(f.worldwide_cr)}</p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}