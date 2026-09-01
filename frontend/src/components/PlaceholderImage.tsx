import type { CSSProperties, ReactNode } from 'react'
import './PlaceholderImage.css'

interface PlaceholderImageProps {
  label: string
  gradient: string
  className?: string
  style?: CSSProperties
  children?: ReactNode
}

/**
 * Stands in for real salon photography until it's available.
 * Swap for a real <img> per spot once real photos are available.
 */
export default function PlaceholderImage({
  label,
  gradient,
  className,
  style,
  children,
}: PlaceholderImageProps) {
  const classes = ['placeholder-image', className].filter(Boolean).join(' ')

  return (
    <div className={classes} style={{ background: gradient, ...style }}>
      <span className="placeholder-image__label">{label}</span>
      {children}
    </div>
  )
}
