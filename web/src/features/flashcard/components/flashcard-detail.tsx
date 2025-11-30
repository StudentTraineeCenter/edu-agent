import {
  flashcardDetailStateAtom,
  resetAtom,
  setShowAnswerAtom,
  submitPendingAttemptsAtom,
  gotItRightAtom,
  gotItWrongAtom,
} from '@/data-acess/flashcard-detail-state'
import { flashcardsAtom } from '@/data-acess/flashcard'
import { useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import React, { useEffect, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Option } from 'effect'
import { flashcardDetailRoute } from '@/routes/_config'
import { FlashcardContent } from './flashcard-content'

type Props = React.ComponentProps<'div'> & {
  flashcardGroupId: string
}

export const FlashcardDetail = ({ flashcardGroupId, ...props }: Props) => {
  const { projectId } = flashcardDetailRoute.useParams()

  const navigate = useNavigate()

  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))

  const reset = useAtomSet(resetAtom)
  const submitPendingAttempts = useAtomSet(submitPendingAttemptsAtom, {
    mode: 'promise',
  })
  const setShowAnswer = useAtomSet(setShowAnswerAtom)
  const gotItRight = useAtomSet(gotItRightAtom)
  const gotItWrong = useAtomSet(gotItWrongAtom)

  const handleClose = useCallback(() => {
    navigate({
      to: '/dashboard/p/$projectId',
      params: { projectId },
    })
  }, [navigate, projectId])

  const handleSubmitPendingAttempts = async () => {
    await submitPendingAttempts({ flashcardGroupId, projectId })
    handleClose()
  }

  const handleRetry = () => {
    reset({ flashcardGroupId })
  }

  // Keyboard shortcuts: R for right, W for wrong, Space to toggle answer
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input/textarea
      const target = event.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return
      }

      // Get current state and flashcards
      const currentState = Option.isSome(stateResult) ? stateResult.value : null
      if (!currentState) return

      // Get current card from Result
      const currentCard =
        flashcardsResult._tag === 'Success'
          ? flashcardsResult.value.data?.[currentState.currentCardIndex]
          : null

      if (!currentCard) return

      const isCardMarked = currentState.markedCardIds.has(currentCard.id)

      // Spacebar toggles show/hide answer
      if (event.code === 'Space' || event.key === ' ') {
        event.preventDefault()
        setShowAnswer({ flashcardGroupId, show: !currentState.showAnswer })
        return
      }

      // Only handle right/wrong shortcuts when answer is shown and card is not marked
      if (!currentState.showAnswer || isCardMarked) return

      if (event.key === 'r' || event.key === 'R') {
        event.preventDefault()
        gotItRight({ flashcardGroupId, projectId })
      } else if (event.key === 'w' || event.key === 'W') {
        event.preventDefault()
        gotItWrong({ flashcardGroupId, projectId })
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [
    projectId,
    stateResult,
    flashcardsResult,
    flashcardGroupId,
    setShowAnswer,
    gotItRight,
    gotItWrong,
  ])

  useEffect(() => {
    reset({ flashcardGroupId })
  }, [flashcardGroupId, reset])

  if (!projectId) return null

  return (
    <div className="flex flex-col flex-1 min-h-0" {...props}>
      <FlashcardContent
        flashcardGroupId={flashcardGroupId}
        projectId={projectId}
        onSubmit={handleSubmitPendingAttempts}
        onRetry={handleRetry}
        onClose={handleClose}
      />
    </div>
  )
}
