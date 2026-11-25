const MONEY = new Map<string, Intl.NumberFormat>();

function moneyFormatter(currency: string): Intl.NumberFormat {
  const cached = MONEY.get(currency);
  if (cached) return cached;
  const formatter = new Intl.NumberFormat("en-US", { style: "currency", currency });
  MONEY.set(currency, formatter);
  return formatter;
}

export function formatMoney(amount: string | number | null | undefined, currency: string): string {
  if (amount === null || amount === undefined || amount === "") return "—";
  const value = typeof amount === "number" ? amount : Number(amount);
  if (!Number.isFinite(value)) return "—";
  return moneyFormatter(currency).format(value);
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  return new Intl.DateTimeFormat("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

export function percentDelta(part: string | null | undefined, whole: string | null | undefined): number | null {
  if (part == null || whole == null || part === "" || whole === "") return null;
  const base = Number(whole);
  const value = Number(part);
  if (!Number.isFinite(base) || !Number.isFinite(value) || base === 0) return null;
  return ((value - base) / base) * 100;
}

export function formatPercent(value: number): string {
  const absolute = Math.abs(value);
  const digits = absolute >= 10 ? 0 : 1;
  return `${absolute.toFixed(digits)}%`;
}
