import { useMutation } from '@tanstack/react-query'
import { ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { analysesApi } from '@/api/endpoints'
import { Button } from '@/components/ui/button'

export function FeedbackButtons({ analysisId }: { analysisId: string }) {
  const [given, setGiven] = useState<'agree' | 'disagree' | null>(null)

  const mutation = useMutation({
    mutationFn: (verdict: 'agree' | 'disagree') => analysesApi.feedback(analysisId, verdict),
    onSuccess: (_data, verdict) => {
      setGiven(verdict)
      toast.success('Thanks for the feedback.')
    },
    onError: () => toast.error('Could not submit feedback. Please try again.'),
  })

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">Was this assessment helpful?</span>
      <Button
        variant={given === 'agree' ? 'default' : 'outline'}
        size="icon"
        onClick={() => mutation.mutate('agree')}
        disabled={mutation.isPending || given !== null}
        aria-label="Agree with this assessment"
      >
        <ThumbsUp className="size-4" />
      </Button>
      <Button
        variant={given === 'disagree' ? 'default' : 'outline'}
        size="icon"
        onClick={() => mutation.mutate('disagree')}
        disabled={mutation.isPending || given !== null}
        aria-label="Disagree with this assessment"
      >
        <ThumbsDown className="size-4" />
      </Button>
    </div>
  )
}
