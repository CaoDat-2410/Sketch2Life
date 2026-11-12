export const MIN_CHILD_AGE_MONTHS = 0;
export const MAX_CHILD_AGE_MONTHS = 155;

export function normalizeChildAgeMonths(ageMonths) {
  if (!Number.isFinite(ageMonths)) return MIN_CHILD_AGE_MONTHS;
  return Math.max(MIN_CHILD_AGE_MONTHS, Math.min(MAX_CHILD_AGE_MONTHS, Math.trunc(ageMonths)));
}

export function splitChildAgeMonths(ageMonths) {
  const boundedAgeMonths = normalizeChildAgeMonths(ageMonths);
  return {
    years: Math.floor(boundedAgeMonths / 12),
    months: boundedAgeMonths % 12,
  };
}

export function formatChildAge(ageMonths) {
  const {years, months} = splitChildAgeMonths(ageMonths);
  if (years === 0) return `${months} tháng`;
  return months === 0 ? `${years} tuổi` : `${years} tuổi ${months} tháng`;
}

export function adjustChildAgeByYears(ageMonths, delta) {
  const {years, months} = splitChildAgeMonths(ageMonths);
  const nextYears = Math.max(0, Math.min(12, years + Math.trunc(delta)));
  return normalizeChildAgeMonths(nextYears * 12 + months);
}

export function adjustChildAgeByMonths(ageMonths, delta) {
  return normalizeChildAgeMonths(normalizeChildAgeMonths(ageMonths) + Math.trunc(delta));
}
