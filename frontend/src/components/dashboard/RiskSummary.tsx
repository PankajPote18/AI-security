import { AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react'
import type { Classification, RiskLevel } from '@/api/types'
import { Progress } from '@/components/ui/progress'

const LEVEL_META: Record<RiskLevel, { color: string; label: string; icon: typeof CheckCircle2 }> = {
  low: { color: 'var(--status-good)', label: 'Low risk', icon: CheckCircle2 },
  medium: { color: 'var(--status-warning)', label: 'Medium risk', icon: AlertTriangle },
  high: { color: 'var(--status-critical)', label: 'High risk', icon: ShieldAlert },
}

const CLASSIFICATION_LABEL: Record<Classification, string> = {
  likely_legitimate: 'Likely legitimate',
  suspicious: 'Suspicious',
  likely_phishing: 'Likely phishing',
}

interface Props {
  riskScore: number
  riskLevel: RiskLevel
  classification: Classification
}

export function RiskSummary({ riskScore, riskLevel, classification }: Props) {
  const meta = LEVEL_META[riskLevel]
  const Icon = meta.icon

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Icon className="size-8 shrink-0" style={{ color: meta.color }} aria-hidden />
        <div>
          <p className="text-3xl font-semibold tabular-nums text-foreground">{riskScore.toFixed(0)}</p>
          <p className="text-sm text-muted-foreground">out of 100</p>
        </div>
        <div className="ml-auto flex flex-col items-end gap-1 text-right">
          <span className="text-sm font-medium" style={{ color: meta.color }}>
            {meta.label}
          </span>
          <span className="text-sm text-muted-foreground">{CLASSIFICATION_LABEL[classification]}</span>
        </div>
      </div>
      <Progress value={riskScore} className="h-2" indicatorStyle={{ backgroundColor: meta.color }} />
    </div>
  )
}
