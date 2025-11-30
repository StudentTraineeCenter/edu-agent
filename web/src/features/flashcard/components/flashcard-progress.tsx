import { Progress } from '@/components/ui/progress'
import { useAtomValue, Result } from '@effect-atom/atom-react'
import { flashcardDetailStateAtom } from '@/data-acess/flashcard-detail-state'
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

  const currentCardIdx = Option.isSome(stateResult)
    ? stateResult.value.currentCardIndex
    : 0

  const totalCount = useMemo(() => {
    if (!Result.isSuccess(flashcardsResult)) return 0
    const { data } = flashcardsResult.value
    return data.length
  }, [flashcardsResult])

  const progressPercentage = useMemo(() => {
    if (Option.isNone(stateResult) || !totalCount) return 0

    const { currentCardIndex } = stateResult.value

    return ((currentCardIndex + 1) / totalCount) * 100
  }, [totalCount, stateResult])

  return (
    <>
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Card {currentCardIdx + 1} of {totalCount}
        </span>
        <span>{Math.round(progressPercentage)}% complete</span>
      </div>

      <Progress value={progressPercentage} className="h-2" />
    </>
  )
}
