import { CheckCircle, XCircle, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAtomValue, useAtomSet, Result } from '@effect-atom/atom-react'
import {
  flashcardDetailStateAtom,
  setShowAnswerAtom,
  gotItRightAtom,
  gotItWrongAtom,
  gotItWithQualityAtom,
} from '@/data-acess/flashcard-detail-state'
import { flashcardsAtom, flashcardGroupAtom } from '@/data-acess/flashcard'
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
  const groupResult = useAtomValue(flashcardGroupAtom(flashcardGroupId))

  const setShowAnswer = useAtomSet(setShowAnswerAtom)
  const gotItRight = useAtomSet(gotItRightAtom)
  const gotItWrong = useAtomSet(gotItWrongAtom)
  const gotItWithQuality = useAtomSet(gotItWithQualityAtom)

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const showAnswer = state?.showAnswer ?? false

  const spacedRepetitionEnabled =
    Result.isSuccess(groupResult) &&
    groupResult.value.flashcard_group?.spaced_repetition_enabled === true

  const currentCard = useMemo(() => {
    if (!Result.isSuccess(flashcardsResult) || Option.isNone(stateResult))
      return null

    const { currentCardIndex } = stateResult.value
    const { data } = flashcardsResult.value

    return data[currentCardIndex]
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

  const handleQualityRating = (quality: number) => {
    gotItWithQuality({ flashcardGroupId, projectId, quality })
  }

  return (
    <div className="flex items-center justify-center pt-8 pb-4">
      <div className="flex flex-col gap-4 items-center">
        <Button
          onClick={handleToggleAnswer}
          className="px-6"
          variant={showAnswer ? 'secondary' : 'default'}
        >
          <span>{showAnswer ? 'Hide Answer' : 'Show Answer'}</span>
        </Button>

        {!isCardMarked && showAnswer && (
          <>
            {spacedRepetitionEnabled ? (
              <div className="flex flex-col gap-2 items-center">
                <p className="text-sm text-muted-foreground mb-2">
                  How well did you know this?
                </p>
                <div className="flex gap-2 flex-wrap justify-center">
                  {[0, 1, 2, 3, 4, 5].map((quality) => (
                    <Button
                      key={quality}
                      onClick={() => handleQualityRating(quality)}
                      variant="outline"
                      size="sm"
                      className="min-w-[60px]"
                    >
                      <Star
                        className={`h-4 w-4 mr-1 ${
                          quality >= 3 ? 'fill-yellow-400 text-yellow-400' : ''
                        }`}
                      />
                      <span>{quality}</span>
                    </Button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  0 = Complete blackout, 5 = Perfect response
                </p>
              </div>
            ) : (
              <div className="flex gap-2">
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
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
