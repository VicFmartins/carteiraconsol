export function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2
  }).format(value);
}

export function formatNumber(value: number, maximumFractionDigits = 0) {
  return new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits
  }).format(value);
}

export function formatPercent(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(value);
}

export function formatDate(value: string) {
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(date);
}

export function formatDateTime(value: string) {
  const date = new Date(value);
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}
