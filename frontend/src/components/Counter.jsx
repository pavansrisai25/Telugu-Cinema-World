import { useEffect, useRef, useState } from "react";
import { animate, useInView, useReducedMotion } from "framer-motion";

export default function Counter({ value, decimals = 0, prefix = "", suffix = "" }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (value == null) return;
    if (reduce) {
      setShown(value);
      return;
    }
    if (!inView) return;
    const controls = animate(0, value, { duration: 1.2, ease: "easeOut", onUpdate: setShown });
    return () => controls.stop();
  }, [value, inView, reduce]);

  if (value == null) return <span>Not available</span>;

  const fmt = (n) =>
    `${prefix}${n.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;

  return (
    <span ref={ref}>
      <span aria-hidden="true">{fmt(shown)}</span>
      <span className="sr-only">{fmt(value)}</span>
    </span>
  );
}