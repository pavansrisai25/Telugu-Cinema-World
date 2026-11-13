export default function PageShell({ title, subtitle, children }) {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-16 pt-8">
      <h1 className="font-display text-3xl font-bold text-white sm:text-4xl">{title}</h1>
      {subtitle && <p className="mt-2 max-w-3xl text-muted">{subtitle}</p>}
      <div className="mt-8 space-y-8">{children}</div>
    </div>
  );
}

export function Card({ title, children }) {
  return (
    <section className="rounded-xl border border-line bg-panel p-4 sm:p-5">
      {title && <h2 className="mb-4 font-display text-xl text-white">{title}</h2>}
      {children}
    </section>
  );
}

export function Note({ children }) {
  return <p className="mt-3 text-xs leading-relaxed text-muted">{children}</p>;
}

export function StateMessage({ loading, error }) {
  if (loading) return <p className="text-muted">Loading…</p>;
  if (error) {
    return (
      <p role="alert" className="rounded-lg border border-line bg-panel p-4 text-muted">
        {error.status ? `The API returned an error (${error.status}). ` : "Can't reach the API. "}
        Start the backend: <code className="text-gold">uvicorn app.main:app --reload</code>
      </p>
    );
  }
  return null;
}