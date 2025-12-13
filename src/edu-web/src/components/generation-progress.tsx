'use client'

import { Loader2Icon } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

export type ProgressStage =
  | 'searching'
  | 'analyzing'
  | 'generating'
  | 'mapping'
  | 'structuring'
  | 'writing'
  | 'building'
  | 'done'

type GenerationProgressProps = {
  status: ProgressStage
  message: string
  error?: string
  className?: string
}

const stageProgress: Record<ProgressStage, number> = {
  searching: 20,
  analyzing: 40,
  generating: 60,
  mapping: 40,
  structuring: 40,
  writing: 80,
  building: 60,
  done: 100,
}

const stageLabels: Record<ProgressStage, string> = {
  searching: 'Searching',
  analyzing: 'Analyzing',
  generating: 'Generating',
  mapping: 'Mapping',
  structuring: 'Structuring',
  writing: 'Writing',
  building: 'Building',
  done: 'Complete',
}

export function GenerationProgress({
  status,
  message,
  error,
  className,
}: GenerationProgressProps) {
  const progress = stageProgress[status] || 0
  const isDone = status === 'done'
  const hasError = !!error

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="flex items-center gap-3">
        {!isDone && !hasError && (
          <Loader2Icon className="size-4 animate-spin text-primary" />
        )}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium">
              {hasError ? 'Error' : stageLabels[status]}
            </span>
            <span className="text-xs text-muted-foreground">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      </div>
      <div className="text-sm text-muted-foreground">
        {hasError ? (
          <span className="text-destructive">{error}</span>
        ) : (
          <span>{message}</span>
        )}
      </div>
    </div>
  )
}
