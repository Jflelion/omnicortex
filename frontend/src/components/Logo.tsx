export function Logo({ className = 'h-8 w-8' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="8" className="fill-indigo-600" />
      <circle cx="16" cy="16" r="6" fill="none" stroke="white" strokeWidth="2.5" />
      <circle cx="16" cy="16" r="2" fill="white" />
    </svg>
  )
}
