import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FeatureContributionOut } from '@/api/types'

// Diverging pair from the project's validated default palette (references/palette.md):
// blue <-> red, categorical slots 1 and 8. Positive SHAP values push the prediction toward
// phishing (risk up); negative values push it toward legitimate (risk down).
const RISK_UP = 'var(--chart-risk-up)'
const RISK_DOWN = 'var(--chart-risk-down)'

interface Props {
  contributions: FeatureContributionOut[]
}

function formatFeatureName(feature: string): string {
  return feature.replace(/_/g, ' ')
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: FeatureContributionOut }[] }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md">
      <p className="font-medium text-popover-foreground">{formatFeatureName(point.feature)}</p>
      <p className="text-muted-foreground">
        {point.shap_value > 0 ? 'Increases' : 'Decreases'} risk by {Math.abs(point.shap_value).toFixed(3)}
      </p>
    </div>
  )
}

export function ShapContributionChart({ contributions }: Props) {
  if (contributions.length === 0) {
    return <p className="text-sm text-muted-foreground">No feature contributions available.</p>
  }

  const data = [...contributions].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).reverse()

  return (
    <div>
      <div className="mb-2 flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: RISK_UP }} />
          Increases risk
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: RISK_DOWN }} />
          Decreases risk
        </span>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(160, data.length * 32)}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 32, top: 4, bottom: 4 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="feature"
            tickFormatter={formatFeatureName}
            width={140}
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--muted)', opacity: 0.4 }} />
          <Bar dataKey="shap_value" radius={4} maxBarSize={20}>
            {data.map((entry) => (
              <Cell key={entry.feature} fill={entry.shap_value > 0 ? RISK_UP : RISK_DOWN} />
            ))}
            <LabelList
              dataKey="shap_value"
              position="right"
              formatter={(value: unknown) => (typeof value === 'number' ? value.toFixed(3) : '')}
              className="fill-foreground text-xs"
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
