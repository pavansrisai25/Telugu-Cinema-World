import { Link } from "react-router-dom";
import {
  CartesianGrid, LabelList, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import PageShell, { Card, Note, StateMessage } from "../components/PageShell";
import { useApi } from "../hooks/useApi";
import { AXIS, GRID } from "../lib/chart";
import { crore, croreRange } from "../lib/format";

const roiText = (p) =>
  p.roi_min != null ? `${p.roi.toFixed(1)}× (to ${p.roi_min.toFixed(1)}×)` : `${p.roi.toFixed(1)}×`;

function PointTip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-line bg-panel p-2 text-xs">
      <p className="font-semibold text-gold">{p.title} ({p.year})</p>
      <p>Budget: {croreRange(p.budget_cr, p.budget_max_cr)}</p>
      <p>Worldwide: {crore(p.worldwide_cr)}</p>
      <p>ROI: {roiText(p)}</p>
    </div>
  );
}

export default function BudgetVsCollection() {
  const { data, error, loading } = useApi("/api/analytics/budget-vs-collection");

  if (loading || error) {
    return <PageShell title="Budget vs collection"><StateMessage loading={loading} error={error} /></PageShell>;
  }

  const points = data.points;
  const maxBudget = Math.max(0, ...points.map((p) => p.budget_cr));
  const byRoi = [...points].sort((a, b) => b.roi - a.roi);

  return (
    <PageShell
      title="Budget vs collection"
      subtitle="Each dot is a film with both a Reported budget and a Reported worldwide gross. Dots above the dashed line grossed more than their budget."
    >
      <Card title="Budget (x) vs worldwide gross (y), in ₹ crore">
        {points.length > 0 ? (
          <div role="img" aria-label="Scatter plot of budget against worldwide gross. The table below has the same data.">
            <ResponsiveContainer width="100%" height={420}>
              <ScatterChart margin={{ top: 16, right: 24, left: 8, bottom: 24 }}>
                <CartesianGrid stroke={GRID} />
                <XAxis
                  type="number" dataKey="budget_cr" name="Budget" {...AXIS}
                  domain={[0, "auto"]} label={{ value: "Budget (₹ crore)", position: "insideBottom", offset: -12, fill: "#a7a7bb" }}
                />
                <YAxis
                  type="number" dataKey="worldwide_cr" name="Worldwide" {...AXIS}
                  domain={[0, "auto"]} width={64} tickFormatter={(v) => v.toLocaleString("en-IN")}
                />
                <ReferenceLine
                  segment={[{ x: 0, y: 0 }, { x: maxBudget, y: maxBudget }]}
                  stroke="#a7a7bb" strokeDasharray="6 4"
                />
                <Tooltip content={<PointTip />} cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={points} fill="#f5b942">
                  <LabelList dataKey="title" position="top" fill="#ececf4" fontSize={11}
                             formatter={(v) => v.split(":")[0]} />
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-muted">Not available</p>
        )}
        <Note>
          The x position uses the low end of a reported budget range. The dashed line is gross = budget.
          Gross is not the producer's profit. {data.excluded_films} released film(s) are left out because
          they lack a budget or a worldwide figure. {data.note}
        </Note>
      </Card>

      <Card title="Return on investment (worldwide gross ÷ budget)">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <caption className="sr-only">Budget, worldwide gross and ROI for each film</caption>
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th scope="col" className="px-2 py-1">Film</th>
                <th scope="col" className="px-2 py-1">Budget</th>
                <th scope="col" className="px-2 py-1">Worldwide</th>
                <th scope="col" className="px-2 py-1">ROI</th>
              </tr>
            </thead>
            <tbody>
              {byRoi.map((p) => (
                <tr key={p.id} className="border-t border-line">
                  <td className="px-2 py-1"><Link className="hover:text-gold" to={`/film/${p.id}`}>{p.title}</Link> <span className="text-muted">({p.year})</span></td>
                  <td className="px-2 py-1">{croreRange(p.budget_cr, p.budget_max_cr)}</td>
                  <td className="px-2 py-1">{crore(p.worldwide_cr)}</td>
                  <td className="px-2 py-1 text-gold-soft">{roiText(p)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </PageShell>
  );
}