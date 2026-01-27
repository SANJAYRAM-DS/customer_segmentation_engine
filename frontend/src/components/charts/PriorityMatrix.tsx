import { cn } from '../../lib/utils';

interface PriorityMatrixProps {
  data: {
    quadrants: {
      name: string;
      customers: number;
      avgClv: number;
      avgRisk: number;
    }[];
  };
  onQuadrantClick?: (quadrant: string) => void;
}

export function PriorityMatrix({ data, onQuadrantClick }: PriorityMatrixProps) {
  const getQuadrantConfig = (name: string) => {
    switch (name) {
      case 'High Value - Retain':
        return {
          position: 'top-right',
          bgColor: 'bg-danger/10',
          borderColor: 'border-danger/30',
          textColor: 'text-danger',
          label: 'Retain',
          sublabel: 'High Value, High Risk',
        };
      case 'High Value - Grow':
        return {
          position: 'top-left',
          bgColor: 'bg-success/10',
          borderColor: 'border-success/30',
          textColor: 'text-success',
          label: 'Grow',
          sublabel: 'High Value, Low Risk',
        };
      case 'Low Value - Nurture':
        return {
          position: 'bottom-left',
          bgColor: 'bg-info/10',
          borderColor: 'border-info/30',
          textColor: 'text-info',
          label: 'Nurture',
          sublabel: 'Low Value, Low Risk',
        };
      case 'Low Value - Monitor':
        return {
          position: 'bottom-right',
          bgColor: 'bg-muted',
          borderColor: 'border-muted-foreground/30',
          textColor: 'text-muted-foreground',
          label: 'Monitor',
          sublabel: 'Low Value, High Risk',
        };
      default:
        return {
          position: '',
          bgColor: 'bg-muted',
          borderColor: 'border-muted',
          textColor: 'text-muted-foreground',
          label: name,
          sublabel: '',
        };
    }
  };

  const orderedQuadrants = [
    data.quadrants.find(q => q.name === 'High Value - Grow'),
    data.quadrants.find(q => q.name === 'High Value - Retain'),
    data.quadrants.find(q => q.name === 'Low Value - Nurture'),
    data.quadrants.find(q => q.name === 'Low Value - Monitor'),
  ].filter(Boolean);

  return (
    <div className="w-full">
      {/* Axis Labels */}
      <div className="flex items-center justify-center mb-2">
        <span className="text-xs text-muted-foreground">← Low Risk</span>
        <span className="mx-4 text-xs font-medium text-foreground">Churn Risk</span>
        <span className="text-xs text-muted-foreground">High Risk →</span>
      </div>

      <div className="flex">
        {/* Y-Axis Label */}
        <div className="flex flex-col items-center justify-center mr-2">
          <span className="text-xs text-muted-foreground rotate-180 writing-mode-vertical">High Value</span>
          <div className="h-8" />
          <span className="text-xs text-muted-foreground rotate-180 writing-mode-vertical">Low Value</span>
        </div>

        {/* Matrix Grid */}
        <div className="flex-1 grid grid-cols-2 gap-3">
          {orderedQuadrants.map((quadrant) => {
            if (!quadrant) return null;
            const config = getQuadrantConfig(quadrant.name);
            return (
              <button
                key={quadrant.name}
                onClick={() => onQuadrantClick?.(quadrant.name)}
                className={cn(
                  'p-4 rounded-lg border-2 text-left transition-all hover:shadow-md',
                  config.bgColor,
                  config.borderColor
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={cn('font-semibold', config.textColor)}>
                    {config.label}
                  </span>
                  <span className={cn('text-2xl font-bold', config.textColor)}>
                    {quadrant.customers}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">{config.sublabel}</p>
                <div className="flex gap-4 text-xs">
                  <span className="text-muted-foreground">
                    Avg CLV: <span className="font-medium text-foreground">${quadrant.avgClv.toLocaleString()}</span>
                  </span>
                  <span className="text-muted-foreground">
                    Avg Risk: <span className="font-medium text-foreground">{quadrant.avgRisk}%</span>
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <style>{`
        .writing-mode-vertical {
          writing-mode: vertical-rl;
        }
      `}</style>
    </div>
  );
}
