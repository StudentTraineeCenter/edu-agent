import { Progress } from '@/components/ui/progress'
import { useAtomValue, Result } from '@effect-atom/atom-react'
import { flashcardDetailStateAtom, filteredFlashcardsAtom } from '@/data-acess/flashcard-detail-state'
import { flashcardsAtom } from '@/data-acess/flashcard'
import { Option } from 'effect'
import { useMemo } from 'react'

type FlashcardProgressProps = {
  flashcardGroupId: string
}

export const FlashcardProgress = ({
  flashcardGroupId,
}: FlashcardProgressProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))
  const filteredFlashcardsResult = useAtomValue(filteredFlashcardsAtom(flashcardGroupId))

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const currentCardIdx = state?.currentCardIndex ?? 0

  const totalCount = useMemo(() => {
    // Use filtered flashcards if available (for cycle mode)
    if (Result.isSuccess(filteredFlashcardsResult)) {
      return filteredFlashcardsResult.value.length
    }
    if (Result.isSuccess(flashcardsResult)) {
      return flashcardsResult.value.data.length
    }
    return 0
  }, [flashcardsResult, filteredFlashcardsResult])

  const progressPercentage = useMemo(() => {
    if (!state || !totalCount) return 0
    return ((currentCardIdx + 1) / totalCount) * 100
  }, [totalCount, state, currentCardIdx])

  const roundInfo = state?.mode === 'cycle-until-correct' && state.currentRound > 1
    ? `Round ${state.currentRound} - `
    : ''

  return (
    <>
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {roundInfo}Card {currentCardIdx + 1} of {totalCount}
        </span>
        <span>{Math.round(progressPercentage)}% complete</span>
      </div>

      <Progress value={progressPercentage} className="h-2" />
    </>
  )
}
