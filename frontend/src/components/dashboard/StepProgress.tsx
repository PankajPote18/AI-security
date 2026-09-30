import { CheckCircle2, CircleDashed, Loader2, XCircle } from 'lucide-react'
import type { AnalysisStepOut } from '@/api/types'

const STEP_LABELS: Record<string, string> = {
  ml: 'ML classification',
  security_analysis: 'Structural indicators + DNS/RDAP',
  agent: 'Agent investigation',
}

function labelFor(step: string): string {
  if (STEP_LABELS[step]) return STEP_LABELS[step]
  if (step.startsWith('tool:')) return `Tool: ${step.slice(5).replace(/_/g, ' ')}`
  return step
}

export function StepProgress({ steps, analysisStatus }: { steps: AnalysisStepOut[]; analysisStatus: string }) {
  return (
    <ul className="flex flex-col gap-2">
      {steps.map((step, index) => {
        const isRunning = step.status === 'running'
        const isDone = step.status === 'done' || step.status === 'success'
        const isFailed = step.status === 'failed' || step.status === 'error'
        return (
          <li key={`${step.step}-${index}`} className="flex items-center gap-2 text-sm">
            {isRunning && <Loader2 className="size-4 shrink-0 animate-spin text-muted-foreground" />}
            {isDone && <CheckCircle2 className="size-4 shrink-0 text-(--status-good)" />}
            {isFailed && <XCircle className="size-4 shrink-0 text-(--status-critical)" />}
            {!isRunning && !isDone && !isFailed && (
              <CircleDashed className="size-4 shrink-0 text-muted-foreground" />
            )}
            <span className={isFailed ? 'text-destructive' : 'text-foreground'}>{labelFor(step.step)}</span>
            {step.ms != null && <span className="text-muted-foreground">{Math.round(step.ms)}ms</span>}
            {step.error && <span className="text-destructive">- {step.error}</span>}
          </li>
        )
      })}
      {steps.length === 0 && analysisStatus === 'running' && (
        <li className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          {'Starting analysis…'}
        </li>
      )}
    </ul>
  )
}
