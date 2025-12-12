import {
  flashcardDetailStateAtom,
  currentFlashcardAtom,
} from '@/features/flashcard/state/flashcard-detail-state'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Loader2Icon } from 'lucide-react'
import { Option } from 'effect'
import { FlashcardCompletionScreen } from './flashcard-completion-screen'
import { FlashcardCard } from './flashcard-card'
import { FlashcardControls } from './flashcard-controls'
import { FlashcardProgress } from './flashcard-progress'

type FlashcardContentProps = {
  flashcardGroupId: string
  projectId: string
  onSubmit: () => void
  onRetry: () => void
  onRetryWrong: (wrongIds: string[]) => void
  onClose: () => void
}

export const FlashcardContent = ({
  flashcardGroupId,
  projectId,
  onSubmit,
  onRetry,
  onRetryWrong,
  onClose,
}: FlashcardContentProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const currentCard = useAtomValue(
    currentFlashcardAtom({ projectId, flashcardGroupId }),
  )

  const state = Option.isSome(stateResult) ? stateResult.value : null

  if (!state) {
    return (
      <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading flashcards...</span>
      </div>
    )
  }

  // Session is complete when queue is empty
  if (state.queue.length === 0 || state.isCompleted) {
    return (
      <FlashcardCompletionScreen
        onSubmit={onSubmit}
        onRetry={onRetry}
        onRetryWrong={onRetryWrong}
        onClose={onClose}
        flashcardGroupId={flashcardGroupId}
        projectId={projectId}
      />
    )
  }

  if (!currentCard) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">No flashcards available</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col space-y-12 flex-1 min-h-0 overflow-auto p-4">
      <FlashcardProgress flashcardGroupId={flashcardGroupId} />

      {Result.builder(currentCard)
        .onSuccess((card) => (
          <FlashcardCard
            flashcardGroupId={flashcardGroupId}
            question={card?.question ?? ''}
            answer={card?.answer ?? ''}
          />
        ))
        .onInitialOrWaiting(() => (
          <div className="flex flex-1 items-center justify-center">
            <Loader2Icon className="size-4 animate-spin" />
            <span>Loading flashcard...</span>
          </div>
        ))
        .render()}

      <FlashcardControls
        flashcardGroupId={flashcardGroupId}
        projectId={projectId}
      />
    </div>
  )
}
