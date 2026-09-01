import { motion, useReducedMotion } from 'motion/react'
import type { MouseEventHandler, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import './Button.css'

const MotionLink = motion.create(Link)

type ButtonVariant = 'solid' | 'outline' | 'text' | 'glass'

interface ButtonProps {
  children: ReactNode
  variant?: ButtonVariant
  href?: string
  to?: string
  type?: 'button' | 'submit'
  disabled?: boolean
  onClick?: MouseEventHandler
  fullWidth?: boolean
  className?: string
}

export default function Button({
  children,
  variant = 'solid',
  href,
  to,
  type = 'button',
  disabled,
  onClick,
  fullWidth,
  className,
}: ButtonProps) {
  const prefersReducedMotion = useReducedMotion()
  const classes = ['btn', `btn--${variant}`, fullWidth && 'btn--full', className]
    .filter(Boolean)
    .join(' ')
  const hoverProps = prefersReducedMotion
    ? {}
    : {
        whileHover: { scale: 1.02 },
        whileTap: { scale: 0.98 },
        transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] as const },
      }

  if (to) {
    return (
      <MotionLink className={classes} to={to} onClick={onClick} {...hoverProps}>
        {children}
      </MotionLink>
    )
  }

  if (href) {
    return (
      <motion.a className={classes} href={href} onClick={onClick} {...hoverProps}>
        {children}
      </motion.a>
    )
  }

  return (
    <motion.button
      className={classes}
      type={type}
      disabled={disabled}
      onClick={onClick}
      {...hoverProps}
    >
      {children}
    </motion.button>
  )
}
