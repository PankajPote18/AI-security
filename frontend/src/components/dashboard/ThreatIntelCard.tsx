import { ExternalLink, ShieldAlert, ShieldCheck, ShieldQuestion } from 'lucide-react'
import type { ThreatIntelOut } from '@/api/types'
import { Badge } from '@/components/ui/badge'

const STATUS_META: Record<ThreatIntelOut['status'], { icon: typeof ShieldCheck; color: string; label: string }> = {
  listed: { icon: ShieldAlert, color: 'var(--status-critical)', label: 'Listed as malicious' },
  not_listed: { icon: ShieldCheck, color: 'var(--status-good)', label: 'Not listed' },
  unavailable: { icon: ShieldQuestion, color: 'var(--muted-foreground)', label: 'Unavailable' },
}

export function ThreatIntelCard({ entries }: { entries: ThreatIntelOut[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No threat-intelligence lookups were performed.</p>
  }

  return (
    <ul className="flex flex-col gap-3">
      {entries.map((entry) => {
        const meta = STATUS_META[entry.status]
        const Icon = meta.icon
        return (
          <li key={entry.provider} className="flex items-start gap-2.5 rounded-md border p-3 text-sm">
            <Icon className="mt-0.5 size-4 shrink-0" style={{ color: meta.color }} aria-hidden />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium capitalize">{entry.provider}</span>
                <span style={{ color: meta.color }}>{meta.label}</span>
              </div>
              {entry.threat_type && (
                <p className="text-muted-foreground">
                  Threat type: <span className="font-mono">{entry.threat_type}</span>
                </p>
              )}
              {entry.tags.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {entry.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
              {entry.status === 'unavailable' && entry.error && (
                <p className="text-muted-foreground">
                  {entry.error === 'not_configured' ? 'Provider not configured' : entry.error}
                </p>
              )}
              {entry.reference_url && (
                <a
                  href={entry.reference_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-primary hover:underline"
                >
                  Reference <ExternalLink className="size-3" />
                </a>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
