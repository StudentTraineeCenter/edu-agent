import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

type FlashcardNavigationProps = {
  isFirstCard: boolean
  isLastCard: boolean
  showAnswer: boolean
  onPrevious: () => void
  onNext: () => void
  onToggleAnswer: () => void
}

export const FlashcardNavigation = ({
  isFirstCard,
  isLastCard,
  showAnswer,
  onPrevious,
  onNext,
  onToggleAnswer,
}: FlashcardNavigationProps) => {
  return (
    <div className="flex items-center justify-between pt-8 pb-4">
      <Button
        onClick={onPrevious}
        disabled={isFirstCard}
        variant="outline"
        className="flex items-center gap-2"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </Button>

      <div className="flex gap-2">
        {!showAnswer ? (
          <Button onClick={onToggleAnswer} className="px-6">
            Show Answer
          </Button>
        ) : (
          <Button onClick={onToggleAnswer} variant="secondary" className="px-6">
            Hide Answer
          </Button>
        )}
      </div>

      <Button
        onClick={onNext}
        disabled={isLastCard}
        variant="outline"
        className="flex items-center gap-2"
      >
        Next
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
