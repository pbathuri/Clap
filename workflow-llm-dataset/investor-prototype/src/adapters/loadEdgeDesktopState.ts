import type { EdgeDesktopLoadResult, EdgeDesktopSnapshot } from './edgeDesktopTypes';

const CACHE_KEY = 'edge_desktop_snapshot_v1';
const DEFAULT_TIMEOUT_MS = 14_000;
const DEFAULT_CACHE_TTL_MS = 120_000;
const PRESENTER_CACHE_TTL_MS = 45 * 60 * 1000;

function parseCache(): { at: number; data: EdgeDesktopSnapshot } | null {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const o = JSON.parse(raw) as { at: number; data: EdgeDesktopSnapshot };
    if (!o?.at || !o?.data) return null;
    return o;
  } catch {
    return null;
  }
}

function writeCache(data: EdgeDesktopSnapshot) {
  try {
    sessionStorage.setItem(
      CACHE_KEY,
      JSON.stringify({ at: Date.now(), data })
    );
  } catch {
    /* quota */
  }
}

function presenterLongCache(): boolean {
  if (typeof window === 'undefined') return false;
  if (new URLSearchParams(window.location.search).get('presenter') === '1')
    return true;
  return import.meta.env.VITE_PRESENTER_LONG_CACHE === '1';
}

/** TTL for session cache: longer in presenter mode (rehearsal). */
export function effectiveEdgeCacheTtlMs(): number {
  return presenterLongCache() ? PRESENTER_CACHE_TTL_MS : DEFAULT_CACHE_TTL_MS;
}

/** Any cached snapshot (ignore TTL) for stale-while-revalidate UI. */
export function peekEdgeDesktopCache(): {
  at: number;
  data: EdgeDesktopSnapshot;
} | null {
  return parseCache();
}

function fetchWithTimeout(
  url: string,
  ms: number,
  signal?: AbortSignal
): Promise<Response> {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  const onAbort = () => c.abort();
  if (signal) signal.addEventListener('abort', onAbort);
  return fetch(url, { signal: c.signal }).finally(() => {
    clearTimeout(t);
    if (signal) signal.removeEventListener('abort', onAbort);
  });
}

export interface LoadOptions {
  cacheTtlMs?: number;
  timeoutMs?: number;
  staticSnapshotPath?: string;
  signal?: AbortSignal;
}

/**
 * Load order: valid cache → API → static file → null (caller uses mock).
 * Respects AbortSignal: aborted fetches return without writing cache.
 */
export async function loadEdgeDesktopState(
  opts: LoadOptions = {}
): Promise<EdgeDesktopLoadResult> {
  if (opts.signal?.aborted) {
    return { snapshot: null, source: 'mock', error: 'aborted' };
  }

  const ttl = opts.cacheTtlMs ?? effectiveEdgeCacheTtlMs();
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  if (ttl > 0) {
    const cached = parseCache();
    if (cached && Date.now() - cached.at < ttl) {
      return { snapshot: cached.data, source: 'cached' };
    }
  }

  let timedOut = false;
  try {
    const res = await fetchWithTimeout(
      '/api/edge-desktop-snapshot',
      timeoutMs,
      opts.signal
    );
    if (opts.signal?.aborted) {
      return { snapshot: null, source: 'mock', error: 'aborted' };
    }
    if (res.ok) {
      const data = (await res.json()) as EdgeDesktopSnapshot;
      writeCache(data);
      return { snapshot: data, source: 'live' };
    }
  } catch (e) {
    const aborted =
      e instanceof Error && e.name === 'AbortError';
    if (aborted) {
      if (opts.signal?.aborted) {
        return { snapshot: null, source: 'mock', error: 'aborted' };
      }
      timedOut = true;
    }
  }

  const staticPath =
    opts.staticSnapshotPath ||
    (import.meta.env.VITE_EDGE_STATIC_SNAPSHOT as string | undefined);
  if (staticPath && !opts.signal?.aborted) {
    try {
      const res = await fetchWithTimeout(
        staticPath.startsWith('/') ? staticPath : `/${staticPath}`,
        6000,
        opts.signal
      );
      if (res.ok) {
        const data = (await res.json()) as EdgeDesktopSnapshot;
        writeCache(data);
        return { snapshot: data, source: 'static_file' };
      }
    } catch {
      /* fall through */
    }
  }

  return {
    snapshot: null,
    source: 'mock',
    error: timedOut ? 'Live snapshot timed out' : 'API unavailable',
    timedOut,
  };
}

export function invalidateEdgeDesktopCache() {
  try {
    sessionStorage.removeItem(CACHE_KEY);
  } catch {
    /* */
  }
}
