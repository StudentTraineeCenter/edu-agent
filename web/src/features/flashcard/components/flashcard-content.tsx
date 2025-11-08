import { flashcardsAtom } from '@/data-acess/flashcard'
import { flashcardDetailStateAtom } from '@/data-acess/flashcard-detail-state'
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
  onClose: () => void
}

export const FlashcardContent = ({
  flashcardGroupId,
  projectId,
  onSubmit,
  onRetry,
  onClose,
}: FlashcardContentProps) => {
  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))

  return Result.builder(flashcardsResult)
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
      const state = Option.isSome(stateResult) ? stateResult.value : null
      if (!state) return null

      const flashcards = result.flashcards ?? []
      const currentCard = flashcards[state.currentCardIndex]

      if (!currentCard || flashcards.length === 0) {
        return (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-muted-foreground">No flashcards available</p>
          </div>
        )
      }

      const allCardsMarked = state.markedCardIds.size === flashcards.length

      if (state.isCompleted || allCardsMarked) {
        return (
          <FlashcardCompletionScreen
            onSubmit={onSubmit}
            onRetry={onRetry}
            onClose={onClose}
            flashcardGroupId={flashcardGroupId}
          />
        )
      }

      return (
        <div className="flex flex-col space-y-12 flex-1 min-h-0 overflow-auto p-4">
          <FlashcardProgress flashcardGroupId={flashcardGroupId} />

          <FlashcardCard
            flashcardGroupId={flashcardGroupId}
            question={currentCard.question}
            answer={currentCard.answer}
          />

          <FlashcardControls
            flashcardGroupId={flashcardGroupId}
            projectId={projectId}
          />
        </div>
      )
    })
    .render()
}
