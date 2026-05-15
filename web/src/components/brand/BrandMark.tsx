type BrandMarkProps = {
  size?: number;
  className?: string;
  variant?: "mono" | "duo";
};

export function BrandMark({ className = "", size = 32, variant = "duo" }: BrandMarkProps) {
  const accentClass = variant === "duo" ? "text-accent" : "text-current";

  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      height={size}
      viewBox="0 0 64 64"
      width={size}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M9 51L25.2 16.8C27.9 11.1 36.1 11.1 38.8 16.8L55 51"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="8"
      />
      <path
        className={accentClass}
        d="M22.5 47H41.5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="7"
      />
      <rect
        className={accentClass}
        height="15"
        rx="3.5"
        stroke="currentColor"
        strokeWidth="4"
        width="8"
        x="38"
        y="31"
      />
      <circle className={accentClass} cx="32" cy="38" fill="currentColor" r="3.7" />
    </svg>
  );
}
