import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Counter from "../components/Counter";
import PageShell, { Card, Note, StateMessage } from "../components/PageShell";
import { useApi } from "../hooks/useApi";
import { AXIS, GRID, TOOLTIP } from "../lib/chart";
import { crore, year } from "../lib/format";

function YearTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-line bg-panel p-2 text-xs">
      <p className="font-semibold text-gold">{label}</p>
      <p>{crore(p.total)}</p>
      <p className="text-muted">{p.covered} have a worldwide figure</p>
    </div>
  );
}

function Stat({ label, children }) {
  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-gold-soft">{children}</p>
    </div>
  );
}

export default function Overview() {
  const { data, error, loading } = useApi("/api/analytics/overview");

  if (loading || error) {
    return <PageShell title="Overview"><StateMessage loading={loading} error={error} /></PageShell>;
  }

  const yearly = data.by_year.map((y) => ({
    year: String(y.year),
    total: y.films_with_worldwide ? y.total_worldwide_cr : null, // missing stays blank, never 0
    covered: `${y.films_with_worldwide} of ${y.films} films`,
  }));
  const totalWorldwide = data.by_year.reduce((s, y) => s + y.total_worldwide_cr, 0);
  const top = data.top_grossers.map((f) => ({ title: f.title, worldwide: f.worldwide_cr }));

  return (
    <PageShell
      title="Overview"
      subtitle="A quick look at the films in this dataset. Money figures are Reported by public sources."
    >
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Films in dataset"><Counter value={data.total_films} /></Stat>
        <Stat label="Released"><Counter value={data.released_films} /></Stat>
        <Stat label="Upcoming"><Counter value={data.upcoming_films} /></Stat>
        <Stat label="With a worldwide figure"><Counter value={data.films_with_worldwide} /></Stat>
      </div>

      <Card title="Reported worldwide gross by release year">
        <p className="mb-3 text-sm text-muted">
          Sum of the headline figures for the films that have one:{" "}
          <span className="text-gold-soft"><Counter value={totalWorldwide} prefix="₹" suffix=" crore" /></span>
        </p>
        <div role="img" aria-label="Bar chart of reported worldwide gross by release year. The table below has the same data.">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={yearly} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="year" {...AXIS} />
              <YAxis {...AXIS} tickFormatter={(v) => v.toLocaleString("en-IN")} width={60} />
              <Tooltip content={<YearTip />} cursor={{ fill: "rgba(245,185,66,0.08)" }} />
              <Bar dataKey="total" fill="#f5b942" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <Note>Years without a bar have no worldwide figure in the dataset. {data.note}</Note>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Worldwide gross by release year</caption>
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th scope="col" className="px-2 py-1">Year</th>
                <th scope="col" className="px-2 py-1">Films</th>
                <th scope="col" className="px-2 py-1">With figure</th>
                <th scope="col" className="px-2 py-1">Total (Reported)</th>
              </tr>
            </thead>
            <tbody>
              {data.by_year.map((y) => (
                <tr key={y.year} className="border-t border-line">
                  <td className="px-2 py-1">{y.year}</td>
                  <td className="px-2 py-1">{y.films}</td>
                  <td className="px-2 py-1">{y.films_with_worldwide}</td>
                  <td className="px-2 py-1">{y.films_with_worldwide ? crore(y.total_worldwide_cr) : "Not available"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Top grossers (Reported worldwide gross)">
        <div role="img" aria-label="Horizontal bar chart of the top grossing films. The list below has the same data.">
          <ResponsiveContainer width="100%" height={Math.max(240, top.length * 36)}>
            <BarChart data={top} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid stroke={GRID} horizontal={false} />
              <XAxis type="number" {...AXIS} tickFormatter={(v) => v.toLocaleString("en-IN")} />
              <YAxis type="category" dataKey="title" width={140} {...AXIS} tick={{ fill: "#ececf4", fontSize: 11 }} />
              <Tooltip {...TOOLTIP} formatter={(v) => [crore(v), "Worldwide"]} cursor={{ fill: "rgba(245,185,66,0.08)" }} />
              <Bar dataKey="worldwide" fill="#f5b942" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ol className="mt-4 grid gap-1 text-sm sm:grid-cols-2">
          {data.top_grossers.map((f) => (
            <li key={f.id}>
              <Link className="hover:text-gold" to={`/film/${f.id}`}>
                {f.title} ({year(f.release_date)})
              </Link>{" "}
              <span className="text-muted">{crore(f.worldwide_cr)}</span>
            </li>
          ))}
        </ol>
      </Card>
    </PageShell>
  );
}