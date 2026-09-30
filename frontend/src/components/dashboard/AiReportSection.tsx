import { Loader2, Sparkles } from 'lucide-react'
import type { SecurityReportOut } from '@/api/types'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface Props {
  report: SecurityReportOut | undefined
  isGenerating: boolean
  canGenerate: boolean
  onGenerate: () => void
}

export function AiReportSection({ report, isGenerating, canGenerate, onGenerate }: Props) {
  if (!report) {
    return (
      <div className="flex flex-col items-start gap-3">
        <p className="text-sm text-muted-foreground">
          Generate a plain-language explanation of this result, grounded in the evidence above. The score and
          classification are never re-decided by this step.
        </p>
        <Button onClick={onGenerate} disabled={!canGenerate || isGenerating}>
          {isGenerating ? (
            <>
              <Loader2 className="size-4 animate-spin" /> {'Generating…'}
            </>
          ) : (
            <>
              <Sparkles className="size-4" /> Generate AI explanation
            </>
          )}
        </Button>
      </div>
    )
  }

  if (report.status === 'failed') {
    return (
      <Alert variant="destructive">
        <AlertTitle>Report generation failed</AlertTitle>
        <AlertDescription>
          {report.error ?? 'The explanation could not be generated. The analysis result above is unaffected.'}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm leading-relaxed">{report.summary}</p>

      {report.indicator_explanations.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium">Indicator explanations</h4>
          <ul className="flex flex-col gap-2">
            {report.indicator_explanations.map((exp) => (
              <li key={exp.indicator_code} className="text-sm">
                <span className="font-mono text-xs text-muted-foreground">{exp.indicator_code}</span>
                <p>{exp.explanation}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.recommendations.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium">Recommendations</h4>
          <ul className="list-inside list-disc text-sm">
            {report.recommendations.map((rec) => (
              <li key={rec}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {report.sources.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium">Sources</h4>
          <div className="flex flex-wrap gap-1.5">
            {report.sources.map((source) => (
              <Badge key={source.chunk_id} variant="outline" className="text-xs">
                {source.title ?? source.doc_id ?? source.chunk_id}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        {report.model_name} &middot; {report.provider} &middot; {Math.round(report.latency_ms)}ms
      </p>
    </div>
  )
}
