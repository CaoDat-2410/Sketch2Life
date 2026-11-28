export const MAX_PARENT_GROUP_INVITATIONS = 50;

export function parseParentPrincipalRefs(value: string): string[] {
  const seen = new Set<string>();
  const refs: string[] = [];

  for (const token of value.split(/[\s,;]+/)) {
    const ref = token.trim();
    if (!ref || seen.has(ref)) continue;
    seen.add(ref);
    refs.push(ref);
  }

  return refs;
}
