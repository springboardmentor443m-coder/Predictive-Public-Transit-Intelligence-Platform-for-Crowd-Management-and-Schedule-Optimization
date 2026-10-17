/**
 * Lightweight in-memory response cache with TTL.
 *
 * Usage:
 *   const data = await cachedFetch('key', () => api.call(), 60_000);
 *
 * First call: executes fetcher, caches result for ttlMs.
 * Subsequent calls within TTL: returns cached value instantly (zero latency).
 * After TTL: returns stale cached value immediately AND triggers a background
 *   refresh so the UI updates without blocking.
 */

interface CacheEntry<T> {
  data: T;
  fetchedAt: number;
  ttlMs: number;
}

const store = new Map<string, CacheEntry<unknown>>();

function get<T>(key: string): CacheEntry<T> | null {
  return (store.get(key) as CacheEntry<T>) ?? null;
}

function set<T>(key: string, data: T, ttlMs: number): void {
  store.set(key, { data, fetchedAt: Date.now(), ttlMs });
}

function isFresh(entry: CacheEntry<unknown>): boolean {
  return Date.now() - entry.fetchedAt < entry.ttlMs;
}

/**
 * Stale-while-revalidate cache fetch.
 *
 * - Returns cached data immediately if available (even if stale).
 * - Always refreshes in background if entry is stale.
 * - onUpdate callback is called when background refresh completes.
 */
export async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs = 30_000,
  onUpdate?: (fresh: T) => void
): Promise<T> {
  const entry = get<T>(key);

  if (entry && isFresh(entry)) {
    // Cache hit — return immediately, no network call
    return entry.data;
  }

  if (entry && !isFresh(entry)) {
    // Stale — return cached immediately, refresh in background
    fetcher()
      .then(fresh => {
        set(key, fresh, ttlMs);
        onUpdate?.(fresh);
      })
      .catch(() => {}); // Swallow background error — stale data still shown
    return entry.data;
  }

  // Cache miss — must await first fetch
  const fresh = await fetcher();
  set(key, fresh, ttlMs);
  return fresh;
}

/** Manually invalidate a cache entry (e.g. after a manual sync). */
export function invalidateCache(key: string): void {
  store.delete(key);
}

/** Invalidate all entries with keys matching a prefix. */
export function invalidateCachePrefix(prefix: string): void {
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) store.delete(key);
  }
}

/** Pre-warm the cache (fire-and-forget). */
export function prefetch<T>(key: string, fetcher: () => Promise<T>, ttlMs = 30_000): void {
  if (get(key) && isFresh(get(key)!)) return;
  fetcher().then(data => set(key, data, ttlMs)).catch(() => {});
}
