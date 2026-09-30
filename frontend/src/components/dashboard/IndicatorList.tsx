import type { IndicatorOut } from '@/api/types'
import { Badge } from '@/components/ui/badge'

const SEVERITY_META: Record<IndicatorOut['severity'], { label: string; color: string }> = {
  high: { label: 'High', color: 'var(--status-critical)' },
  medium: { label: 'Medium', color: 'var(--status-warning)' },
  low: { label: 'Low', color: 'var(--status-good)' },
  info: { label: 'Info', color: 'var(--muted-foreground)' },
}

export function IndicatorList({ indicators }: { indicators: IndicatorOut[] }) {
  if (indicators.length === 0) {
    return <p className="text-sm text-muted-foreground">No structural indicators fired.</p>
  }

  return (
    <ul className="flex flex-col gap-3">
      {indicators.map((indicator) => {
        const severity = SEVERITY_META[indicator.severity]
        return (
          <li key={indicator.code} className="rounded-md border p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className="inline-block size-2 shrink-0 rounded-full"
                style={{ backgroundColor: severity.color }}
                aria-hidden
              />
              <span className="text-sm font-medium">{indicator.title}</span>
              <Badge variant="outline" className="ml-auto text-xs" style={{ color: severity.color, borderColor: severity.color }}>
                {severity.label}
              </Badge>
              {indicator.mitre_technique && (
                <Badge variant="secondary" className="text-xs">
                  {indicator.mitre_technique}
                </Badge>
              )}
            </div>
            <p className="mt-1.5 text-sm text-muted-foreground">{indicator.description}</p>
          </li>
        )
      })}
    </ul>
  )
}
