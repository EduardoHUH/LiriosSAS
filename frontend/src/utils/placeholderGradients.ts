/** Editorial-toned stand-ins for real photography, matching the gradients
 * used throughout the site's design. Cycled by a numeric seed
 * (e.g. a service id) so the same item always gets the same gradient. */
const GRADIENTS = [
  'linear-gradient(170deg, oklch(88% 0.03 95) 0%, oklch(70% 0.05 60) 60%, oklch(50% 0.06 35) 100%)',
  'linear-gradient(170deg, oklch(90% 0.02 90) 0%, oklch(74% 0.05 145) 55%, oklch(48% 0.05 150) 100%)',
  'linear-gradient(170deg, oklch(87% 0.03 70) 0%, oklch(66% 0.05 35) 60%, oklch(44% 0.05 30) 100%)',
  'linear-gradient(165deg, oklch(85% 0.03 95) 0%, oklch(68% 0.05 55) 55%, oklch(48% 0.06 30) 100%)',
  'linear-gradient(175deg, oklch(90% 0.02 90) 0%, oklch(72% 0.05 145) 60%, oklch(50% 0.05 150) 100%)',
]

export function getPlaceholderGradient(seed: number): string {
  const index = ((seed % GRADIENTS.length) + GRADIENTS.length) % GRADIENTS.length
  return GRADIENTS[index]
}
