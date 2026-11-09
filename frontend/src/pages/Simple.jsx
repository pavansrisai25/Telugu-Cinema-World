import { Link } from "react-router-dom";

export function ComingSoon({ title, phase }) {
  return (
    <div className="mx-auto max-w-lg p-12 text-center">
      <h1 className="font-display text-3xl text-white">{title}</h1>
      <p className="mt-2 text-muted">Coming in {phase}.</p>
      <Link to="/" className="mt-4 inline-block text-gold underline">Back to home</Link>
    </div>
  );
}

export function NotFound() {
  return (
    <div className="mx-auto max-w-lg p-12 text-center">
      <h1 className="font-display text-3xl text-white">Page not found</h1>
      <Link to="/" className="mt-4 inline-block text-gold underline">Back to home</Link>
    </div>
  );
}