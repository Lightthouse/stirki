import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  fullWidth?: boolean
}

export function Button({
  variant = 'primary',
  fullWidth = false,
  className = '',
  children,
  ...props
}: ButtonProps) {
  const base = 'btn'
  const variantClass = `btn-${variant}`
  const widthClass = fullWidth ? 'btn-full' : ''

  return (
    <button
      className={`${base} ${variantClass} ${widthClass} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  )
}
