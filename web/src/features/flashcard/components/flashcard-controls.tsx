import { CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAtomValue, useAtomSet, Result } from '@effect-atom/atom-react'
import {
  flashcardDetailStateAtom,
  setShowAnswerAtom,
  gotItRightAtom,
  gotItWrongAtom,
} from '@/data-acess/flashcard-detail-state'
import { flashcardsAtom } from '@/data-acess/flashcard'
import { Option } from 'effect'
import { useMemo } from 'react'

type FlashcardControlsProps = {
  flashcardGroupId: string
  projectId: string
}

export const FlashcardControls = ({
  flashcardGroupId,
  projectId,
}: FlashcardControlsProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))

  const setShowAnswer = useAtomSet(setShowAnswerAtom)
  const gotItRight = useAtomSet(gotItRightAtom)
  const gotItWrong = useAtomSet(gotItWrongAtom)

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const showAnswer = state?.showAnswer ?? false

  const currentCard = useMemo(() => {
    if (!Result.isSuccess(flashcardsResult) || Option.isNone(stateResult))
      return null

    const { currentCardIndex } = stateResult.value
    const { flashcards } = flashcardsResult.value

    return flashcards[currentCardIndex]
  }, [flashcardsResult, stateResult])

  const isCardMarked = useMemo(() => {
    if (!currentCard || Option.isNone(stateResult)) return false

    const { markedCardIds } = stateResult.value

    return markedCardIds.has(currentCard.id)
  }, [currentCard, stateResult])

  const handleToggleAnswer = () => {
    setShowAnswer({ flashcardGroupId, show: !showAnswer })
  }

  const handleGotItRight = () => {
    gotItRight({ flashcardGroupId, projectId })
  }

  const handleGotItWrong = () => {
    gotItWrong({ flashcardGroupId, projectId })
  }

  return (
    <div className="flex items-center justify-center pt-8 pb-4">
      <div className="flex gap-2">
        <Button
          onClick={handleToggleAnswer}
          className="px-6"
          variant={showAnswer ? 'secondary' : 'default'}
        >
          <span>{showAnswer ? 'Hide Answer' : 'Show Answer'}</span>
        </Button>

        {!isCardMarked && (
          <>
            <Button
              onClick={handleGotItRight}
              variant="default"
              className="px-6 bg-green-600 hover:bg-green-700 text-white"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              <span>Got it right</span>
              <span className="ml-2 text-xs opacity-70">(R)</span>
            </Button>

            <Button
              onClick={handleGotItWrong}
              variant="default"
              className="px-6 bg-red-600 hover:bg-red-700 text-white"
            >
              <XCircle className="h-4 w-4 mr-2" />
              <span>Got it wrong</span>
              <span className="ml-2 text-xs opacity-70">(W)</span>
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
