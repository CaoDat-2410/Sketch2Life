// Follows an opaque cursor list (SRS §21.1 l.1640: default page 25, maximum 100) to its end, so a
// screen never silently stops after the first page. The cursor is passed back unchanged; a repeated
// cursor or the page cap ends the walk instead of looping on a misbehaving server.

export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
}

export const CURSOR_PAGE_LIMIT = 100;
export const MAX_CURSOR_PAGES = 50;

export async function collectCursorPages<T, P extends CursorPage<T> = CursorPage<T>>(
  loadPage: (cursor: string | undefined) => Promise<P>,
  maxPages: number = MAX_CURSOR_PAGES,
): Promise<{ first: P; items: T[] }> {
  const first = await loadPage(undefined);
  const items = [...first.items];
  const seen = new Set<string>();
  let cursor = first.next_cursor;
  let pages = 1;
  while (cursor && !seen.has(cursor) && pages < maxPages) {
    seen.add(cursor);
    const page = await loadPage(cursor);
    items.push(...page.items);
    cursor = page.next_cursor;
    pages += 1;
  }
  return { first, items };
}

export function pageQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [name, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(name, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}
