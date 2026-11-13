import { useEffect, useState } from "react";
import { api } from "../api";

/** Loads `path` and returns { data, error, loading }. A null path means "don't load". */
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: Boolean(path) });

  useEffect(() => {
    if (!path) {
      setState({ data: null, error: null, loading: false });
      return;
    }
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