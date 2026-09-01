/** Picks a "clean" axis step (1/2/5 × 10^n) and returns evenly spaced tick
 * values from 0 up to at least `maxValue`, rounded to
 * clean numbers. */
export function niceTicks(maxValue: number, targetCount = 4): number[] {
  if (maxValue <= 0) return [0]

  const roughStep = maxValue / targetCount
  const magnitude = 10 ** Math.floor(Math.log10(roughStep))
  const normalized = roughStep / magnitude
  const step = (normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10) * magnitude

  const ticks: number[] = []
  for (let value = 0; value <= maxValue + step; value += step) {
    ticks.push(Math.round(value * 100) / 100)
  }
  return ticks
}
