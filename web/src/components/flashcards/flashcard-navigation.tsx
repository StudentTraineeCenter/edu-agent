import { CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

type FlashcardNavigationProps = {
  showAnswer: boolean
  isCardMarked: boolean
  onToggleAnswer: () => void
  onGotItRight?: () => void
  onGotItWrong?: () => void
}

export const FlashcardNavigation = ({
  showAnswer,
  isCardMarked,
  onToggleAnswer,
  onGotItRight,
  onGotItWrong,
}: FlashcardNavigationProps) => {
  return (
    <div className="flex items-center justify-center pt-8 pb-4">
      <div className="flex gap-2">
        {!showAnswer ? (
          <Button onClick={onToggleAnswer} className="px-6">
            Show Answer
          </Button>
        ) : (
          <>
            <Button
              onClick={onToggleAnswer}
              variant="secondary"
              className="px-6"
            >
              Hide Answer
            </Button>
            {!isCardMarked && (
              <>
                {onGotItRight && (
                  <Button
                    onClick={onGotItRight}
                    variant="default"
                    className="px-6 bg-green-600 hover:bg-green-700 text-white"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Got it right{' '}
                    <span className="ml-2 text-xs opacity-70">(R)</span>
                  </Button>
                )}
                {onGotItWrong && (
                  <Button
                    onClick={onGotItWrong}
                    variant="default"
                    className="px-6 bg-red-600 hover:bg-red-700 text-white"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Got it wrong{' '}
                    <span className="ml-2 text-xs opacity-70">(W)</span>
                  </Button>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
