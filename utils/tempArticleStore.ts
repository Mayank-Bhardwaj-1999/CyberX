import type { Article } from '../types/news';

// Ephemeral in-memory article store to pass full objects between routes without serialization issues.
// Entries auto-expire after 5 minutes.
const store = new Map<string, { article: Article; expires: number }>();

const EXPIRY_MS = 5 * 60 * 1000;

function cleanup() {
  const now = Date.now();
  for (const [id, v] of store.entries()) {
    if (v.expires < now) store.delete(id);
  }
}

export function putTempArticle(article: Article): string {
  cleanup();
  const id = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  store.set(id, { article, expires: Date.now() + EXPIRY_MS });
  return id;
}

export function getTempArticle(id: string): Article | undefined {
  cleanup();
  return store.get(id)?.article;
}
