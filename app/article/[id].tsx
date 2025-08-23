import { useEffect } from 'react';
import { useLocalSearchParams, router } from 'expo-router';

export default function ArticleRedirect() {
  const { id } = useLocalSearchParams<{ id: string }>();

  useEffect(() => {
    if (id) {
      // Redirect to the article-view route
      router.replace(`/article-view/${id}`);
    }
  }, [id]);

  return null;
}