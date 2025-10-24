import { flashcardsAtom } from '@/data-acess/flashcard'
import { useAtomValue } from '@effect-atom/atom-react'
import React, { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

type Props = React.ComponentProps<'div'> & {
  flashcardGroupId: string
}

export const FlashcardDetail = ({ flashcardGroupId, ...props }: Props) => {
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)

  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))
  const flashcards =
    flashcardsResult._tag === 'Success' ? flashcardsResult.value.flashcards : []

  const currentCard = flashcards[currentCardIndex]
  const isFirstCard = currentCardIndex === 0
  const isLastCard = currentCardIndex === flashcards.length - 1

  if (!currentCard || flashcards.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <p className="text-muted-foreground">No flashcards available</p>
      </div>
    )
  }

  const toggleAnswer = () => {
    setShowAnswer(!showAnswer)
  }

  const goToPreviousCard = () => {
    if (!isFirstCard) {
      setCurrentCardIndex(currentCardIndex - 1)
      setShowAnswer(false)
    }
  }

  const goToNextCard = () => {
    if (!isLastCard) {
      setCurrentCardIndex(currentCardIndex + 1)
      setShowAnswer(false)
    }
  }

  const progressPercentage = ((currentCardIndex + 1) / flashcards.length) * 100

  return (
    <div className="flex flex-col space-y-12" {...props}>
      {/* Progress indicator */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Card {currentCardIndex + 1} of {flashcards.length}
        </span>
        <span>{Math.round(progressPercentage)}% complete</span>
      </div>

      {/* Progress bar */}
      <Progress value={progressPercentage} className="h-4 my-2" />

      {/* Flashcard content */}
      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-3xl">
          <div
            className="bg-white border rounded-xl shadow-xl p-12 min-h-[420px] flex flex-col justify-center cursor-pointer hover:shadow-2xl transition-shadow"
            onClick={toggleAnswer}
          >
            <div className="space-y-10">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  Question
                </h3>
                <p className="text-lg leading-relaxed">
                  {currentCard.question}
                </p>
              </div>

              {showAnswer && (
                <div className="border-t pt-8">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">
                    Answer
                  </h3>
                  <p className="text-lg leading-relaxed text-green-700">
                    {currentCard.answer}
                  </p>
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

      {/* Navigation */}
      <div className="flex items-center justify-between pt-8">
        <Button
          onClick={goToPreviousCard}
          disabled={isFirstCard}
          variant="outline"
          className="flex items-center gap-2"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>

        <div className="flex gap-2">
          {!showAnswer ? (
            <Button onClick={toggleAnswer} className="px-6">
              Show Answer
            </Button>
          ) : (
            <Button onClick={toggleAnswer} variant="secondary" className="px-6">
              Hide Answer
            </Button>
          )}
        </div>

        <Button
          onClick={goToNextCard}
          disabled={isLastCard}
          variant="outline"
          className="flex items-center gap-2"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
