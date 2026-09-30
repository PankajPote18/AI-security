import type { DomainInfoOut } from '@/api/types'
import { Badge } from '@/components/ui/badge'

export function DomainInfoCard({ domainInfo }: { domainInfo: DomainInfoOut }) {
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
      <div>
        <dt className="text-muted-foreground">Registered domain</dt>
        <dd className="font-medium">{domainInfo.registered_domain}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Registrar</dt>
        <dd className="font-medium">{domainInfo.registrar ?? 'Unknown'}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Domain age</dt>
        <dd className="font-medium">
          {domainInfo.domain_age_days != null ? `${domainInfo.domain_age_days} days` : 'Unknown'}
        </dd>
      </div>
      <div>
        <dt className="text-muted-foreground">DNS resolved</dt>
        <dd className="font-medium">{domainInfo.dns_resolved ? 'Yes' : 'No'}</dd>
      </div>
      <div className="col-span-2">
        <dt className="mb-1.5 text-muted-foreground">DNS records</dt>
        <dd className="flex flex-wrap gap-1.5">
          {domainInfo.dns_records
            .filter((r) => r.values.length > 0)
            .map((record) => (
              <Badge key={record.record_type} variant="secondary" className="font-mono text-xs">
                {record.record_type}: {record.values.join(', ')}
              </Badge>
            ))}
          {domainInfo.dns_records.every((r) => r.values.length === 0) && (
            <span className="text-muted-foreground">No records resolved</span>
          )}
        </dd>
      </div>
    </dl>
  )
}
