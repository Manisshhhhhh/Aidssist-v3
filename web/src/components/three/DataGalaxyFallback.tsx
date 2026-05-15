type DataGalaxyFallbackProps = {
  className?: string;
  compact?: boolean;
};

export function DataGalaxyFallback({ className = "", compact = false }: DataGalaxyFallbackProps) {
  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
    >
      <div className={compact ? "data-galaxy-fallback compact" : "data-galaxy-fallback"} />
    </div>
  );
}
