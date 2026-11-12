export const MIN_CHILD_AGE_MONTHS = 36;
export const MAX_CHILD_AGE_MONTHS = 120;
export const CHILD_AGE_RANGE_MESSAGE = 'Tuổi phải nằm trong khoảng 36–120 tháng.';

export function isSupportedChildAge(ageMonths: number): boolean {
  return Number.isInteger(ageMonths) && ageMonths >= MIN_CHILD_AGE_MONTHS && ageMonths <= MAX_CHILD_AGE_MONTHS;
}
