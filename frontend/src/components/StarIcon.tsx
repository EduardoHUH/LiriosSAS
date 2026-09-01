interface StarIconProps {
  filled: boolean
  size?: number
}

export default function StarIcon({ filled, size = 14 }: StarIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 1.5l1.9 4.2 4.6.5-3.4 3.2.9 4.5L8 11.7l-4 2.2.9-4.5-3.4-3.2 4.6-.5L8 1.5z"
        fill={filled ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="1"
        strokeLinejoin="round"
      />
    </svg>
  )
}
