import { useAtom, useAtomSet } from '@effect-atom/atom-react'
import {
  flashcardDetailStateAtom,
  setShowAnswerAtom,
} from '@/data-acess/flashcard-detail-state'
import { Option } from 'effect'

type FlashcardCardProps = {
  flashcardGroupId: string
  question: string
  answer: string
}

export const FlashcardCard = ({
  flashcardGroupId,
  question,
  answer,
}: FlashcardCardProps) => {
  const [stateResult] = useAtom(flashcardDetailStateAtom(flashcardGroupId))
  const state = Option.isSome(stateResult) ? stateResult.value : null
  const showAnswer = state?.showAnswer ?? false

  const setShowAnswer = useAtomSet(setShowAnswerAtom)

  const handleToggle = () => {
    setShowAnswer({ flashcardGroupId, show: !showAnswer })
  }

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="w-full max-w-3xl">
        <div
          className="bg-card border rounded-xl shadow-lg p-12 min-h-[420px] flex flex-col justify-center cursor-pointer hover:shadow-xl transition-shadow"
          onClick={handleToggle}
        >
          <div className="space-y-10">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">
                Question
              </h3>
              <p className="text-lg leading-relaxed">{question}</p>
            </div>

            {showAnswer && (
              <div className="border-t pt-8">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  Answer
                </h3>
                <p className="text-lg leading-relaxed text-primary">{answer}</p>
              </div>
            )}

            {!showAnswer && (
              <div className="text-center">
                <p className="text-muted-foreground text-sm">
                  Click to reveal answer
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
