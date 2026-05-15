type JobProgressBarProps = {
  progress: number;
};

export function JobProgressBar({ progress }: JobProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, progress));

  return (
    <div className="h-2 overflow-hidden rounded-full bg-surface1" aria-label={`Job progress ${clamped}%`}>
      <div
        className="h-full rounded-full bg-primary transition-all duration-500"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
