import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useParams } from 'react-router-dom'
import { ApiError } from '@/api/client'
import { analysesApi } from '@/api/endpoints'
import { AiReportSection } from '@/components/dashboard/AiReportSection'
import { DomainInfoCard } from '@/components/dashboard/DomainInfoCard'
import { FeedbackButtons } from '@/components/dashboard/FeedbackButtons'
import { IndicatorList } from '@/components/dashboard/IndicatorList'
import { RiskSummary } from '@/components/dashboard/RiskSummary'
import { ShapContributionChart } from '@/components/dashboard/ShapContributionChart'
import { StepProgress } from '@/components/dashboard/StepProgress'
import { ThreatIntelCard } from '@/components/dashboard/ThreatIntelCard'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const IN_PROGRESS = new Set(['pending', 'running'])
const POLL_INTERVAL_MS = 2500

export function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const analysisQuery = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => analysesApi.get(id!),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data && IN_PROGRESS.has(query.state.data.status) ? POLL_INTERVAL_MS : false),
  })

  const analysis = analysisQuery.data
  const isComplete = analysis?.status === 'completed'

  const reportQuery = useQuery({
    queryKey: ['report', id],
    queryFn: () => analysesApi.report.get(id!),
    enabled: !!id && isComplete,
    retry: false,
  })

  const generateReport = useMutation({
    mutationFn: () => analysesApi.report.generate(id!),
    onSuccess: (report) => queryClient.setQueryData(['report', id], report),
  })

  if (analysisQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground">
        <Loader2 className="mr-2 size-5 animate-spin" /> Loading…
      </div>
    )
  }

  if (analysisQuery.isError || !analysis) {
    const message = analysisQuery.error instanceof ApiError ? analysisQuery.error.message : 'Analysis not found.'
    return (
      <Alert variant="destructive">
        <AlertTitle>Could not load this analysis</AlertTitle>
        <AlertDescription>{message}</AlertDescription>
      </Alert>
    )
  }

  const report = reportQuery.data

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="break-all text-xl font-semibold">{analysis.url}</h1>
          {analysis.mode === 'deep' && <Badge variant="secondary">Deep analysis</Badge>}
        </div>
        {analysis.degraded && (
          <p className="mt-1 text-sm text-(--status-warning)">
            Some evidence sources were unavailable; this result may be incomplete.
          </p>
        )}
      </div>

      {IN_PROGRESS.has(analysis.status) && (
        <Card>
          <CardHeader>
            <CardTitle>Analyzing…</CardTitle>
          </CardHeader>
          <CardContent>
            <StepProgress steps={analysis.steps} analysisStatus={analysis.status} />
          </CardContent>
        </Card>
      )}

      {analysis.status === 'failed' && (
        <Alert variant="destructive">
          <AlertTitle>Analysis failed</AlertTitle>
          <AlertDescription>{analysis.error ?? 'An unexpected error occurred.'}</AlertDescription>
        </Alert>
      )}

      {isComplete && analysis.risk_score != null && analysis.risk_level && analysis.classification && (
        <>
          <Card>
            <CardContent className="pt-6">
              <RiskSummary
                riskScore={analysis.risk_score}
                riskLevel={analysis.risk_level}
                classification={analysis.classification}
              />
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            {analysis.ml_analysis && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">ML analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="mb-4 text-sm text-muted-foreground">
                    {analysis.ml_analysis.model_name} &middot; probability{' '}
                    {(analysis.ml_analysis.probability * 100).toFixed(1)}%
                  </p>
                  <ShapContributionChart contributions={analysis.ml_analysis.top_contributions} />
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Security indicators</CardTitle>
              </CardHeader>
              <CardContent>
                <IndicatorList indicators={analysis.indicators} />
              </CardContent>
            </Card>

            {analysis.domain_info && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Domain information</CardTitle>
                </CardHeader>
                <CardContent>
                  <DomainInfoCard domainInfo={analysis.domain_info} />
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Threat intelligence</CardTitle>
              </CardHeader>
              <CardContent>
                <ThreatIntelCard entries={analysis.threat_intelligence} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">AI explanation</CardTitle>
            </CardHeader>
            <CardContent>
              <AiReportSection
                report={report}
                isGenerating={generateReport.isPending}
                canGenerate={!reportQuery.isFetching}
                onGenerate={() => generateReport.mutate()}
              />
            </CardContent>
          </Card>

          <div>
            <FeedbackButtons analysisId={analysis.id} />
          </div>
        </>
      )}
    </div>
  )
}
