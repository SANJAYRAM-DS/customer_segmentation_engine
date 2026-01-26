import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function ChartContainer({
  title,
  subtitle,
  action,
  children,
  className,
}: ChartContainerProps) {
  return (
    <div
      className={cn(
        'bg-card rounded-lg border border-border shadow-card animate-fade-in',
        className
      )}
    >
      <div className="flex items-start justify-between p-6 pb-4">
        <div>
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="px-6 pb-6">{children}</div>
    </div>
  );
}
