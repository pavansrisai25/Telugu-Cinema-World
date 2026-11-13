import { useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageShell, { Card, Note, StateMessage } from "../components/PageShell";
import { useApi } from "../hooks/useApi";
import { AXIS, GRID, TOOLTIP } from "../lib/chart";
import { crore } from "../lib/format";

const LANGUAGES = ["Telugu", "Hindi", "Kannada"];

function Cell({ value, percent = false }) {
  if (value == null) return <span className="text-xs text-muted">Not available</span>;
  return <span>{percent ? `${value}%` : crore(value)}</span>;
}

export default function PanIndia() {
  const [language, setLanguage] = useState("Telugu");
  const { data, error, loading } = useApi(`/api/analytics/pan-india?language=${encodeURIComponent(language)}`);

  const picker = (
    <div>
      <label htmlFor="lang" className="mr-2 text-sm text-muted">Language</label>
      <select
        id="lang" value={language} onChange={(e) => setLanguage(e.target.value)}
        className="rounded-lg border border-line bg-panel px-3 py-1.5 text-white"
      >
        {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
      </select>
    </div>
  );

  if (loading || error) {
    return (
      <PageShell title="Pan-India growth">
        {picker}
        <StateMessage loading={loading} error={error} />
      </PageShell>
    );
  }

  const withWorldwide = data.films.filter((f) => f.worldwide_cr != null);
  const chartData = withWorldwide.map((f) => ({ label: `${f.title} (${f.year})`, worldwide: f.worldwide_cr }));
  const noSplits = data.coverage.with_hindi_belt === 0 && data.coverage.with_overseas === 0;

  return (
    <PageShell
      title="Pan-India growth"
      subtitle="How the films of one language grew over time, and how much of the earnings came from the Hindi belt and overseas, where a source states it."
    >
      {picker}

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          ["Films with a Reported figure", `${data.coverage.films} of ${data.coverage.films_in_dataset}`],
          ["With a Hindi-belt figure", data.coverage.with_hindi_belt],
          ["With an overseas figure", data.coverage.with_overseas],
        ].map(([label, n]) => (
          <div key={label} className="rounded-xl border border-line bg-panel p-4">
            <p className="text-sm text-muted">{label}</p>
            <p className="mt-1 text-3xl font-semibold text-gold-soft">{n}</p>
          </div>
        ))}
      </div>

      {noSplits && (
        <div role="note" className="rounded-xl border border-gold/40 bg-gold/10 p-4 text-sm">
          <p className="font-semibold text-gold">No Hindi-belt or overseas splits yet</p>
          <p className="mt-1 text-muted">
            No sourced split is in the database, so those columns show "Not available" instead of an
            estimate. Add rows with market <code>hindi_belt</code> or <code>overseas</code> to{" "}
            <code>backend/data/collections.csv</code> (each with a source), import them, and this page fills in.
          </p>
        </div>
      )}

      <Card title={`${language} films: Reported worldwide gross, in release order`}>
        {chartData.length > 0 ? (
          <div role="img" aria-label="Horizontal bar chart of worldwide gross by film. The table below has the same data.">
            <ResponsiveContainer width="100%" height={Math.max(240, chartData.length * 34)}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
                <CartesianGrid stroke={GRID} horizontal={false} />
                <XAxis type="number" {...AXIS} tickFormatter={(v) => v.toLocaleString("en-IN")} />
                <YAxis type="category" dataKey="label" width={190} {...AXIS} tick={{ fill: "#ececf4", fontSize: 11 }} />
                <Tooltip {...TOOLTIP} formatter={(v) => [crore(v), "Worldwide"]} cursor={{ fill: "rgba(245,185,66,0.08)" }} />
                <Bar dataKey="worldwide" fill="#f5b942" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-muted">Not available</p>
        )}
        <Note>{data.note}</Note>
      </Card>

      <Card title="All figures">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <caption className="sr-only">Collections by market for each {language} film</caption>
            <thead className="text-xs uppercase text-muted">
              <tr>
                {["Film", "Year", "India net", "Hindi belt", "Overseas", "Worldwide", "Hindi-belt share", "Overseas share"].map((h) => (
                  <th key={h} scope="col" className="px-2 py-1">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.films.map((f) => (
                <tr key={f.id} className="border-t border-line">
                  <td className="px-2 py-1"><Link className="hover:text-gold" to={`/film/${f.id}`}>{f.title}</Link></td>
                  <td className="px-2 py-1">{f.year}</td>
                  <td className="px-2 py-1"><Cell value={f.india_net_cr} /></td>
                  <td className="px-2 py-1"><Cell value={f.hindi_belt_cr} /></td>
                  <td className="px-2 py-1"><Cell value={f.overseas_cr} /></td>
                  <td className="px-2 py-1"><Cell value={f.worldwide_cr} /></td>
                  <td className="px-2 py-1"><Cell value={f.hindi_belt_share_pct} percent /></td>
                  <td className="px-2 py-1"><Cell value={f.overseas_share_pct} percent /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </PageShell>
  );
}