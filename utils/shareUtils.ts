import { Share } from 'react-native';
import type { Article } from '../types/news';

export async function shareArticle(article: Article) {
  try {
    const result = await Share.share({
      message: `Check out this news article: ${article.title}\n\n${article.url}`,
      url: article.url,
      title: article.title,
    });

    return result;
  } catch (error) {
    console.error('Error sharing article:', error);
    throw error;
  }
}

export function getShareableText(article: Article): string {
  return `${article.title}\n\nRead more: ${article.url}`;
}
