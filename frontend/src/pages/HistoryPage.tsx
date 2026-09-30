import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { analysesApi } from '@/api/endpoints'
import type { AnalysisSummaryOut, Classification, RiskLevel } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const LEVEL_COLOR: Record<RiskLevel, string> = {
  low: 'var(--status-good)',
  medium: 'var(--status-warning)',
  high: 'var(--status-critical)',
}

const CLASSIFICATION_LABEL: Record<Classification, string> = {
  likely_legitimate: 'Likely legitimate',
  suspicious: 'Suspicious',
  likely_phishing: 'Likely phishing',
}

function StatusBadge({ status }: { status: AnalysisSummaryOut['status'] }) {
  if (status === 'completed') return <Badge variant="secondary">Completed</Badge>
  if (status === 'failed') return <Badge variant="destructive">Failed</Badge>
  return <Badge variant="outline">{status === 'running' ? 'Running' : 'Pending'}</Badge>
}

export function HistoryPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analyses'],
    queryFn: analysesApi.list,
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">History</h1>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 size-5 animate-spin" /> Loading…
        </div>
      )}

      {isError && <p className="text-sm text-destructive">Could not load your analysis history.</p>}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No analyses yet. <Link to="/analyze" className="text-primary hover:underline">Analyze a URL</Link> to get
          started.
        </p>
      )}

      {data && data.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>URL</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Risk score</TableHead>
              <TableHead>Classification</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id} className="cursor-pointer">
                <TableCell className="max-w-xs truncate">
                  <Link to={`/analyses/${row.id}`} className="hover:underline">
                    {row.url}
                  </Link>
                </TableCell>
                <TableCell>
                  <StatusBadge status={row.status} />
                </TableCell>
                <TableCell>
                  {row.risk_score != null && row.risk_level ? (
                    <span className="font-medium tabular-nums" style={{ color: LEVEL_COLOR[row.risk_level] }}>
                      {row.risk_score.toFixed(0)}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell>
                  {row.classification ? (
                    CLASSIFICATION_LABEL[row.classification]
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(row.created_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
