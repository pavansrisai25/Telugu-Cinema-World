import { croreRange, formatDate } from "../lib/format";

/** `data` is a Sourced object from the API (amount_cr, label, source_name, ...). */
export default function Figure({ title, data }) {
  const ok = data && data.amount_cr != null;

  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <p className="text-sm text-muted">{title}</p>
      {ok ? (
        <>
          <p className="mt-1 text-2xl font-semibold text-gold-soft">
            {croreRange(data.amount_cr, data.amount_max_cr)}
          </p>
          <p className="mt-2 text-xs text-muted">
            <span className="mr-2 rounded bg-gold/15 px-1.5 py-0.5 font-medium text-gold">
              {data.label}
            </span>
            {data.source_name && (
              <>
                Source:{" "}
                {data.source_url ? (
                  <a className="underline hover:text-white" href={data.source_url}
                     target="_blank" rel="noopener noreferrer">
                    {data.source_name}
                  </a>
                ) : (
                  data.source_name
                )}
              </>
            )}
            {data.fetched_on && <> · fetched {formatDate(data.fetched_on)}</>}
          </p>
          {data.note && <p className="mt-1 text-xs text-muted">{data.note}</p>}
        </>
      ) : (
        <p className="mt-1 text-xl text-muted">Not available</p>
      )}
    </div>
  );
}