import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  CheckCircle,
  XCircle,
  RotateCcw,
  ArrowLeft,
  CheckCheck,
} from 'lucide-react'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import {
  answeredCardsAtom,
  flashcardDetailStateAtom,
} from '@/features/flashcard/state/flashcard-detail-state'
import { Option } from 'effect'

type FlashcardCompletionScreenProps = {
  flashcardGroupId: string
  projectId: string
  onSubmit: () => void
  onRetry: () => void
  onRetryWrong: (wrongIds: string[]) => void
  onClose: () => void
}

export const FlashcardCompletionScreen = ({
  flashcardGroupId,
  projectId,
  onSubmit,
  onRetry,
  onRetryWrong,
  onClose,
}: FlashcardCompletionScreenProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const answeredCardsResult = useAtomValue(
    answeredCardsAtom({ projectId, flashcardGroupId }),
  )

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const hasPendingPracticeRecords =
    state && Object.keys(state.pendingPracticeRecords).length > 0

  const { correct, incorrect } = Result.isSuccess(answeredCardsResult)
    ? answeredCardsResult.value
    : { correct: [], incorrect: [] }

  const total = correct.length + incorrect.length
  const percentage = total > 0 ? Math.round((correct.length / total) * 100) : 0

  return (
    <div className="flex flex-col flex-1 items-center justify-center p-4">
      <Card className="w-full max-w-2xl p-8">
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center">
              <CheckCheck className="h-12 w-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-semibold">Session Complete</h2>
            <p className="text-muted-foreground">
              You've reviewed all {total} flashcards
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 py-4">
            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <div className="text-2xl font-bold text-green-600">
                  {correct.length}
                </div>
              </div>
              <div className="text-xs text-muted-foreground">Correct</div>
            </div>

            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1.5">
                <XCircle className="h-4 w-4 text-red-600" />
                <div className="text-2xl font-bold text-red-600">
                  {incorrect.length}
                </div>
              </div>
              <div className="text-xs text-muted-foreground">Incorrect</div>
            </div>

            <div className="text-center space-y-1">
              <div className="text-2xl font-bold">{percentage}%</div>
              <div className="text-xs text-muted-foreground">Accuracy</div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3 pt-4">
            {incorrect.length > 0 && (
              <Button
                onClick={() => onRetryWrong(incorrect.map((c) => c.id))}
                size="lg"
                className="w-full"
              >
                Practice incorrect cards ({incorrect.length})
              </Button>
            )}

            <div className="flex gap-3">
              <Button
                onClick={onRetry}
                variant="outline"
                size="lg"
                className="flex-1"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Retry All
              </Button>

              <Button
                onClick={hasPendingPracticeRecords ? onSubmit : onClose}
                variant="outline"
                size="lg"
                className="flex-1"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                {hasPendingPracticeRecords ? 'Save & Close' : 'Close'}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
