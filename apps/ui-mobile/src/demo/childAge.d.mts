export const MIN_CHILD_AGE_MONTHS: number;
export const MAX_CHILD_AGE_MONTHS: number;
export function normalizeChildAgeMonths(ageMonths: number): number;
export function splitChildAgeMonths(ageMonths: number): { years: number; months: number };
export function formatChildAge(ageMonths: number): string;
export function adjustChildAgeByYears(ageMonths: number, delta: number): number;
export function adjustChildAgeByMonths(ageMonths: number, delta: number): number;
