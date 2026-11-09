import { useState } from "react";

export default function Poster({ src, title, className = "" }) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div
        role="img"
        aria-label={`${title} (no poster available)`}
        className={`flex items-center justify-center bg-panel-2 p-2 text-center text-sm text-muted ${className}`}
      >
        {title}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={`${title} poster`}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`object-cover ${className}`}
    />
  );
}