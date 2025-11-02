import { flashcardsAtom } from '@/data-acess/flashcard'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import React, { useEffect, useState } from 'react'
import { Loader2Icon } from 'lucide-react'
import { FlashcardProgress } from './flashcard-progress'
import { FlashcardCard } from './flashcard-card'
import { FlashcardNavigation } from './flashcard-navigation'

type Props = React.ComponentProps<'div'> & {
  flashcardGroupId: string
}

export const FlashcardDetail = ({ flashcardGroupId, ...props }: Props) => {
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)

  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))

  const toggleAnswer = () => {
    setShowAnswer(!showAnswer)
  }

  const goToPreviousCard = (isFirstCard: boolean) => {
    if (!isFirstCard) {
      setCurrentCardIndex(currentCardIndex - 1)
      setShowAnswer(false)
    }
  }

  const goToNextCard = (isLastCard: boolean) => {
    if (!isLastCard) {
      setCurrentCardIndex(currentCardIndex + 1)
      setShowAnswer(false)
    }
  }

  useEffect(() => {
    setCurrentCardIndex(0)
    setShowAnswer(false)
  }, [flashcardGroupId])

  return (
    <div className="flex flex-col flex-1 min-h-0" {...props}>
      {Result.builder(flashcardsResult)
        .onInitialOrWaiting(() => (
          <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
            <Loader2Icon className="size-4 animate-spin" />
            <span>Loading flashcards...</span>
          </div>
        ))
        .onFailure(() => (
          <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
            <span>Failed to load flashcards</span>
          </div>
        ))
        .onSuccess((result) => {
          const flashcards = result.flashcards ?? []
          const currentCard = flashcards[currentCardIndex]
          const isFirstCard = currentCardIndex === 0
          const isLastCard = currentCardIndex === flashcards.length - 1

          if (!currentCard || flashcards.length === 0) {
            return (
              <div className="flex flex-1 items-center justify-center">
                <p className="text-muted-foreground">No flashcards available</p>
              </div>
            )
          }

          return (
            <div className="flex flex-col space-y-12 flex-1 min-h-0 overflow-auto p-4">
              <FlashcardProgress
                currentIndex={currentCardIndex}
                totalCount={flashcards.length}
              />

              <FlashcardCard
                question={currentCard.question}
                answer={currentCard.answer}
                showAnswer={showAnswer}
                onToggle={toggleAnswer}
              />

              <FlashcardNavigation
                isFirstCard={isFirstCard}
                isLastCard={isLastCard}
                showAnswer={showAnswer}
                onPrevious={() => goToPreviousCard(isFirstCard)}
                onNext={() => goToNextCard(isLastCard)}
                onToggleAnswer={toggleAnswer}
              />
            </div>
          )
        })
        .render()}
    </div>
  )
}
