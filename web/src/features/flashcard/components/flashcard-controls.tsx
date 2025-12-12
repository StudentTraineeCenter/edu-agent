import { CheckCircle, XCircle, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import {
  flashcardDetailStateAtom,
  setShowAnswerAtom,
  gotItRightAtom,
  gotItWrongAtom,
  currentFlashcardAtom,
} from '@/features/flashcard/state/flashcard-detail-state'
import { Option } from 'effect'

type FlashcardControlsProps = {
  flashcardGroupId: string
  projectId: string
}

export const FlashcardControls = ({
  flashcardGroupId,
  projectId,
}: FlashcardControlsProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const currentCard = useAtomValue(
    currentFlashcardAtom({ projectId, flashcardGroupId }),
  )

  const setShowAnswer = useAtomSet(setShowAnswerAtom)
  const gotItRight = useAtomSet(gotItRightAtom)
  const gotItWrong = useAtomSet(gotItWrongAtom)

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const showAnswer = state?.showAnswer ?? false
  const hasCurrentCard = currentCard !== null

  const handleToggleAnswer = () => {
    setShowAnswer({ flashcardGroupId, show: !showAnswer })
  }

  const handleGotItWrong = () => {
    gotItWrong({ flashcardGroupId, projectId })
  }

  const handleGotItRight = () => {
    gotItRight({ flashcardGroupId, projectId })
  }

  if (!hasCurrentCard) return null

  return (
    <div className="flex items-center justify-center pt-8 pb-4">
      <div className="flex gap-3 items-center">
        <Button
          onClick={handleGotItWrong}
          variant="default"
          size="lg"
          className="px-8 bg-red-600 hover:bg-red-700 text-white"
        >
          <XCircle className="h-4 w-4 mr-2" />
          <span>Not yet</span>
          <span className="ml-2 text-xs opacity-70">(W)</span>
        </Button>

        <Button
          onClick={handleToggleAnswer}
          variant="outline"
          size="lg"
          className="px-8"
        >
          {showAnswer ? (
            <>
              <EyeOff className="h-4 w-4 mr-2" />
              <span>Hide</span>
              <span className="ml-2 text-xs opacity-70">(Space)</span>
            </>
          ) : (
            <>
              <Eye className="h-4 w-4 mr-2" />
              <span>Show Answer</span>
              <span className="ml-2 text-xs opacity-70">(Space)</span>
            </>
          )}
        </Button>

        <Button
          onClick={handleGotItRight}
          variant="default"
          size="lg"
          className="px-8 bg-green-600 hover:bg-green-700 text-white"
        >
          <CheckCircle className="h-4 w-4 mr-2" />
          <span>Got it</span>
          <span className="ml-2 text-xs opacity-70">(R)</span>
        </Button>
      </div>
    </div>
  )
}
