/** Normalize Vietnamese topic labels for comparisons without changing display text. */
export function normalizeTopicLabel(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[đĐ]/g, (letter) => (letter === 'Đ' ? 'D' : 'd'))
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

/**
 * Catalog selections must echo their selected ID and equivalent label. A custom
 * label is resolved by the backend, which may return a catalog's canonical name.
 */
export function isResolvedTopicConsistent(input: {
  selectedTopicId: string;
  selectedTopic: string;
  resolvedTopicId: string;
  resolvedTopic: string;
}): boolean {
  const selectedTopicId = input.selectedTopicId.trim();
  const selectedTopic = input.selectedTopic.trim();
  const resolvedTopicId = input.resolvedTopicId.trim();
  const resolvedTopic = input.resolvedTopic.trim();
  if (!selectedTopicId || !selectedTopic || !resolvedTopicId || !resolvedTopic) return false;
  if (selectedTopicId === 'custom') return true;
  return selectedTopicId === resolvedTopicId
    && normalizeTopicLabel(selectedTopic) === normalizeTopicLabel(resolvedTopic);
}
