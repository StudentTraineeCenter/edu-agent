import { Progress } from '@/components/ui/progress'
import { useAtomValue } from '@effect-atom/atom-react'
import { flashcardDetailStateAtom } from '@/features/flashcard/state/flashcard-detail-state'
import { Option } from 'effect'
import { useMemo } from 'react'

type FlashcardProgressProps = {
  flashcardGroupId: string
}

export const FlashcardProgress = ({
  flashcardGroupId,
}: FlashcardProgressProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))

  const state = Option.isSome(stateResult) ? stateResult.value : null

  if (!state) {
    return null
  }

  // Use initialCardIds to get the true total (unique cards at start)
  // If initialCardIds is empty (old state), fall back to current queue + attempted
  const initialQueueSize =
    state.initialCardIds.size ||
    state.queue.length +
      state.sessionCorrectIds.size +
      state.sessionWrongIds.size

  // Count both correct and incorrect as "completed" (attempted)
  const completedInSession =
    state.sessionCorrectIds.size + state.sessionWrongIds.size

  const progressPercentage = useMemo(() => {
    if (!initialQueueSize) return 0
    return (completedInSession / initialQueueSize) * 100
  }, [completedInSession, initialQueueSize])

  if (initialQueueSize === 0) {
    return null
  }

  return (
    <>
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {completedInSession} of {initialQueueSize} completed
        </span>
        <span>{Math.round(progressPercentage)}% complete</span>
      </div>

      <Progress value={progressPercentage} className="h-2" />
    </>
  )
}
