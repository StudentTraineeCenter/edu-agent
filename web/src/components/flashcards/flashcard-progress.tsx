import { Progress } from '@/components/ui/progress'

type FlashcardProgressProps = {
  currentIndex: number
  totalCount: number
}

export const FlashcardProgress = ({
  currentIndex,
  totalCount,
}: FlashcardProgressProps) => {
  const progressPercentage = ((currentIndex + 1) / totalCount) * 100

  return (
    <>
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Card {currentIndex + 1} of {totalCount}
        </span>
        <span>{Math.round(progressPercentage)}% complete</span>
      </div>
      <Progress value={progressPercentage} className="h-2" />
    </>
  )
}
