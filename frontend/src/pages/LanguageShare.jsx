import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageShell, { Card, Note, StateMessage } from "../components/PageShell";
import { useApi } from "../hooks/useApi";
import { AXIS, GRID, TOOLTIP, langColor } from "../lib/chart";
import { crore } from "../lib/format";

export default function LanguageShare() {
  const { data, error, loading } = useApi("/api/analytics/language-share");

  if (loading || error) {
    return <PageShell title="Language share"><StateMessage loading={loading} error={error} /></PageShell>;
  }

  const languages = data.overall.languages.map((l) => l.language);
  const rows = data.years.map((y) => {
    const row = { year: String(y.year) };
    y.languages.forEach((l) => { row[l.language] = l.share_pct; });
    return row;
  });

  return (
    <PageShell
      title="Language share"
      subtitle={`Each language's share of the ${data.basis} among the films in this dataset.`}
    >
      <Card title="Share of worldwide gross by release year">
        <div role="img" aria-label="Stacked bar chart of language share by release year. The table below has the same data.">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="year" {...AXIS} />
              <YAxis {...AXIS} domain={[0, 100]} unit="%" width={48} />
              <Tooltip {...TOOLTIP} formatter={(v, name) => [`${v}%`, name]} cursor={{ fill: "rgba(245,185,66,0.08)" }} />
              <Legend wrapperStyle={{ color: "#ececf4" }} />
              {languages.map((lang, i) => (
                <Bar key={lang} dataKey={lang} stackId="share" fill={langColor(lang, i)} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <Note>
          {data.note} A year with one or two films can swing to 100% for one language, so read the
          film counts in the table below before drawing conclusions.
        </Note>
      </Card>

      <Card title="Overall (all years in the dataset)">
        <ul className="grid gap-3 sm:grid-cols-3">
          {data.overall.languages.map((l, i) => (
            <li key={l.language} className="rounded-lg border border-line bg-panel-2 p-3">
              <p className="flex items-center gap-2 text-sm text-muted">
                <span aria-hidden className="inline-block h-3 w-3 rounded-sm" style={{ background: langColor(l.language, i) }} />
                {l.language}
              </p>
              <p className="mt-1 text-2xl font-semibold text-gold-soft">{l.share_pct}%</p>
              <p className="text-xs text-muted">{l.films} films · {crore(l.total_cr)}</p>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Year-by-year data">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Language share and film counts per release year</caption>
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th scope="col" className="px-2 py-1">Year</th>
                <th scope="col" className="px-2 py-1">Total</th>
                <th scope="col" className="px-2 py-1">Languages (share, film count)</th>
              </tr>
            </thead>
            <tbody>
              {data.years.map((y) => (
                <tr key={y.year} className="border-t border-line">
                  <td className="px-2 py-1">{y.year}</td>
                  <td className="px-2 py-1">{crore(y.total_cr)}</td>
                  <td className="px-2 py-1">
                    {y.languages.map((l) => `${l.language} ${l.share_pct}% (${l.films})`).join(" · ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </PageShell>
  );
}