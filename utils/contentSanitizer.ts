// Utility to clean raw article content of site chrome / artifacts
// Removes share button placeholders, print JS snippets, font resizer text, advertisement markers, and stray [] tokens

export function cleanArticleContent(raw?: string | null): string | null {
  if (!raw) return null;
  let text = raw;

  // Remove javascript print handlers or other inline js artifacts
  text = text.replace(/javascript:if\(window\.print\)window\.print\(\)/gi, '');

  // Remove repeated empty markdown link tokens like []() or []
  text = text.replace(/\[\]\(\)/g, '');
  text = text.replace(/\[\]/g, '');

  // Normalize line endings
  text = text.replace(/\r\n?/g, '\n');

  const lines = text.split('\n');
  const filtered = lines.filter((line) => {
    const trimmed = line.trim();
    if (!trimmed) return true; // keep empty lines for paragraph spacing (we'll collapse later)
    if (/^Font\s+Resizer/i.test(trimmed)) return false;
    if (/^-+\s*Advertisement\s*-+$/i.test(trimmed)) return false;
    if (/^Advertisement$/i.test(trimmed)) return false;
    if (/^-+\s*advertisement\s*-+$/i.test(trimmed)) return false;
    // Single asterisk bullets that are likely category tags (short, few words)
    if (/^\*\s?[A-Za-z &/]+$/.test(trimmed) && trimmed.split(/\s+/).length <= 4) return false;
    // Lines that are only punctuation or link brackets remnants
    if (/^[\[\](){}*]+$/.test(trimmed)) return false;
    return true;
  });

  text = filtered.join('\n');

  // Collapse 3+ newlines to maximum 2
  text = text.replace(/\n{3,}/g, '\n\n');

  return text.trim();
}
