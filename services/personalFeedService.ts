import { GoogleNewsService } from './googleNewsService';
import type { Article } from '../types/news';

// Placeholder for additional site scrapers (extend later)
async function fetchFromCustomSources(topic: string): Promise<Article[]> {
  // Future: fetch domain-specific sources (e.g., vendor blogs) for this topic.
  // Returning empty array keeps interface consistent.
  void topic; // reference to avoid unused param warning
  return [];
}

export async function fetchPersonalizedArticles(topics: string[], limitPerTopic = 10): Promise<Article[]> {
  const uniqueTopics = Array.from(new Set(topics.map(t => t.trim()).filter(Boolean)));
  const all: Article[] = [];
  for (const topic of uniqueTopics) {
    try {
      const google = await GoogleNewsService.searchCyberSecurityNews(topic, limitPerTopic);
      const custom = await fetchFromCustomSources(topic);
      all.push(...google, ...custom);
    } catch (e) {
      console.warn('Personal feed topic fetch failed', topic, e);
    }
  }
  // Deduplicate by URL
  const seen = new Set<string>();
  const deduped: Article[] = [];
  for (const a of all) {
    if (!seen.has(a.url)) {
      seen.add(a.url);
      deduped.push(a);
    }
  }
  // Sort newest first
  return deduped.sort((a,b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime());
}
