import { useState, useEffect } from 'react';

/**
 * SSR-safe hook that tracks a CSS media query.
 * Returns `true` on the server (desktop-first default) and updates on the client.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(true); // SSR default: desktop

  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
