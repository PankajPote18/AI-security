import { useMutation } from '@tanstack/react-query'
import { Loader2, Search, Sparkles } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '@/api/client'
import { analysesApi } from '@/api/endpoints'
import type { AnalysisMode } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const MODES: { value: AnalysisMode; label: string; description: string }[] = [
  {
    value: 'standard',
    label: 'Standard',
    description: 'A fixed pipeline: ML classifier, structural checks, DNS/RDAP, threat intel.',
  },
  {
    value: 'deep',
    label: 'Deep (agent)',
    description: 'An LLM agent chooses which tools to call. Slower, runs in the background.',
  },
]

export function AnalyzePage() {
  const [url, setUrl] = useState('')
  const [mode, setMode] = useState<AnalysisMode>('standard')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: () => analysesApi.analyze(url.trim(), mode),
    onSuccess: (analysis) => navigate(`/analyses/${analysis.id}`),
    onError: (err) => setError(err instanceof ApiError ? err.message : 'Could not start the analysis.'),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!url.trim()) return
    mutation.mutate()
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-2xl font-semibold">Analyze a URL</h1>
      <p className="mb-6 text-muted-foreground">Submit a URL to check for phishing indicators.</p>

      <Card>
        <CardHeader>
          <CardTitle>URL</CardTitle>
          <CardDescription>Include the scheme, e.g. https://example.com/login</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              type="text"
              placeholder="https://"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              autoFocus
            />

            <div className="grid grid-cols-2 gap-3">
              {MODES.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setMode(option.value)}
                  className={cn(
                    'flex flex-col items-start gap-1 rounded-md border p-3 text-left transition-colors',
                    mode === option.value ? 'border-primary bg-primary/5' : 'hover:bg-muted/50',
                  )}
                >
                  <span className="flex items-center gap-1.5 text-sm font-medium">
                    {option.value === 'deep' && <Sparkles className="size-3.5 text-primary" />}
                    {option.label}
                  </span>
                  <span className="text-xs text-muted-foreground">{option.description}</span>
                </button>
              ))}
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" disabled={mutation.isPending || !url.trim()}>
              {mutation.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> {'Starting…'}
                </>
              ) : (
                <>
                  <Search className="size-4" /> Analyze
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
