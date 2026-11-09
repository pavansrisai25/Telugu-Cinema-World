import { useEffect, useState } from "react";
import { api } from "../api";

/** Loads `path` and returns { data, error, loading }. Cancels stale requests. */
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    const ctrl = new AbortController();
    setState({ data: null, error: null, loading: true });
    api(path, { signal: ctrl.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== "AbortError") setState({ data: null, error, loading: false });
      });
    return () => ctrl.abort();
  }, [path]);

  return state;
}