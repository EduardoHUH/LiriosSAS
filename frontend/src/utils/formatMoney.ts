/** Formats a DRF DecimalField string (e.g. "1250.00") as Honduran Lempiras,
 * e.g. "L 1,250". Money is never treated as a float for arithmetic here --
 * this only formats a value the backend already computed. */
export function formatMoney(amount: string): string {
  const value = Number(amount)
  const formatted = new Intl.NumberFormat('es-HN', {
    minimumFractionDigits: value % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(value)
  return `L ${formatted}`
}
