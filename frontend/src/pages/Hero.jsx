import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ROLE_LABEL } from "../components/CastCard";
import Counter from "../components/Counter";
import PageShell, { Card, Note, StateMessage } from "../components/PageShell";
import Poster from "../components/Poster";
import { useApi } from "../hooks/useApi";
import { AXIS, GRID, TOOLTIP } from "../lib/chart";
import { NA, crore, croreRange, year } from "../lib/format";

function Photo({ src, name }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <div aria-hidden className="flex h-40 w-32 items-center justify-center rounded-xl bg-panel-2 text-3xl font-semibold text-muted">
        {name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
      </div>
    );
  }
  return <img src={src} alt={name} onError={() => setFailed(true)} className="h-40 w-32 rounded-xl object-cover" />;
}

export default function Hero() {
  const { id } = useParams();
  const { data: p, error, loading } = useApi(`/api/people/${id}`);

  if (loading || error) {
    return (
      <PageShell title={error?.status === 404 ? "Person not found" : "Filmography"}>
        <StateMessage loading={loading} error={error?.status === 404 ? null : error} />
        {error?.status === 404 && <Link className="text-gold underline" to="/">Back to home</Link>}
      </PageShell>
    );
  }

  const roiRows = p.filmography
    .filter((c) => c.roi != null)
    .map((c) => ({ label: `${c.film.title} (${year(c.film.release_date)})`, roi: c.roi }));

  return (
    <PageShell title={p.name} subtitle={p.known_for ? `Known for: ${p.known_for}` : undefined}>
      <div className="flex flex-wrap items-center gap-6">
        <Photo src={p.photo_url} name={p.name} />
        <div className="grid flex-1 grid-cols-2 gap-4 sm:max-w-md">
          <div className="rounded-xl border border-line bg-panel p-4">
            <p className="text-sm text-muted">Films in dataset</p>
            <p className="mt-1 text-3xl font-semibold text-gold-soft"><Counter value={p.stats.films} /></p>
          </div>
          <div className="rounded-xl border border-line bg-panel p-4">
            <p className="text-sm text-muted">Average ROI</p>
            <p className="mt-1 text-3xl font-semibold text-gold-soft">
              {p.stats.average_roi != null ? <Counter value={p.stats.average_roi} decimals={1} suffix="×" /> : NA}
            </p>
            <p className="mt-1 text-xs text-muted">across {p.stats.films_with_roi} film(s)</p>
          </div>
        </div>
      </div>
      <Note>{p.stats.note}. Roles come from TMDB billing order plus manual corrections.</Note>

      {roiRows.length > 0 && (
        <Card title="Return on investment by film">
          <div role="img" aria-label="Bar chart of return on investment per film. The filmography below has the same data.">
            <ResponsiveContainer width="100%" height={Math.max(200, roiRows.length * 38)}>
              <BarChart data={roiRows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
                <CartesianGrid stroke={GRID} horizontal={false} />
                <XAxis type="number" {...AXIS} unit="×" />
                <YAxis type="category" dataKey="label" width={190} {...AXIS} tick={{ fill: "#ececf4", fontSize: 11 }} />
                <Tooltip {...TOOLTIP} formatter={(v) => [`${v.toFixed(1)}×`, "ROI"]} cursor={{ fill: "rgba(245,185,66,0.08)" }} />
                <Bar dataKey="roi" fill="#f5b942" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <Note>ROI = worldwide gross ÷ budget, from Reported figures. Films missing either figure are left out.</Note>
        </Card>
      )}

      <Card title="Filmography">
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {p.filmography.map((c) => (
            <li key={`${c.film.id}-${c.role}`}>
              <Link to={`/film/${c.film.id}`} className="flex gap-3 rounded-xl border border-line bg-panel-2 p-3 hover:border-gold">
                <Poster src={c.film.poster_url} title={c.film.title} className="h-24 w-16 shrink-0 rounded" />
                <div className="min-w-0 text-sm">
                  <p className="truncate font-medium text-white">{c.film.title}</p>
                  <p className="text-xs text-muted">{year(c.film.release_date)} · {c.film.language}</p>
                  <p className="mt-1 text-xs text-gold">
                    {ROLE_LABEL[c.role] ?? c.role}{c.character_name ? ` as ${c.character_name}` : ""}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    Budget {c.budget_cr != null ? croreRange(c.budget_cr) : NA}
                    <br />Worldwide {crore(c.worldwide_cr)}
                    <br />ROI {c.roi != null ? `${c.roi.toFixed(1)}×` : NA}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </PageShell>
  );
}