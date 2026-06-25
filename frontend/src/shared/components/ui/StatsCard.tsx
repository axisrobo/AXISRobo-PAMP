import clsx from 'clsx';

interface StatsCardProps {
  label: string;
  value: number | string;
  color?: string;
  borderColor?: string;
  className?: string;
}

export function StatsCard({ label, value, color = 'text-primary-blue', borderColor, className }: StatsCardProps) {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg border border-border-light p-4 flex flex-col items-center justify-center min-w-[120px]',
        'shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all',
        borderColor && 'border-t-[3px]',
        className
      )}
      style={borderColor ? { borderTopColor: borderColor } : undefined}
    >
      <span className={clsx('text-3xl font-bold', color)}>{value}</span>
      <span className="text-xs text-text-secondary mt-1 text-center">{label}</span>
    </div>
  );
}
