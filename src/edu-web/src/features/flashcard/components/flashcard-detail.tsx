import { useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import React, { useCallback, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Option } from 'effect'
import { FlashcardContent } from './flashcard-content'
import { flashcardDetailRoute } from '@/routes/_config'
import {
  currentFlashcardAtom,
  flashcardDetailStateAtom,
  gotItRightAtom,
  gotItWrongAtom,
  initializeQueueAtom,
  resetAtom,
  resetWrongAtom,
  setShowAnswerAtom,
  submitPendingPracticeRecordsAtom,
} from '@/features/flashcard/state/flashcard-detail-state'

type Props = React.ComponentProps<'div'> & {
  flashcardGroupId: string
}

export const FlashcardDetail = ({ flashcardGroupId, ...props }: Props) => {
  const { projectId } = flashcardDetailRoute.useParams()

  const navigate = useNavigate()

  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const currentCard = useAtomValue(
    currentFlashcardAtom({ projectId, flashcardGroupId }),
  )

  const reset = useAtomSet(resetAtom)
  const initializeQueue = useAtomSet(initializeQueueAtom)
  const resetWrong = useAtomSet(resetWrongAtom)
  const submitPendingPracticeRecords = useAtomSet(
    submitPendingPracticeRecordsAtom,
    {
      mode: 'promise',
    },
  )
  const setShowAnswer = useAtomSet(setShowAnswerAtom)
  const gotItRight = useAtomSet(gotItRightAtom)
  const gotItWrong = useAtomSet(gotItWrongAtom)

  const handleClose = useCallback(() => {
    navigate({
      to: '/dashboard/p/$projectId',
      params: { projectId },
    })
  }, [navigate, projectId])

  const handleSubmitPendingPracticeRecords = async () => {
    await submitPendingPracticeRecords({ flashcardGroupId, projectId })
    handleClose()
  }

  const handleRetry = () => {
    reset({ flashcardGroupId })
    initializeQueue({ projectId, flashcardGroupId, includeMastered: false })
  }

  const handleRetryWrong = (wrongIds: Array<string>) => {
    resetWrong({
      flashcardGroupId,
      wrongCardIds: new Set(wrongIds),
    })
  }

  // Keyboard shortcuts: Spacebar for toggle answer, R for "Got it", W for "Not yet"
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input/textarea
      const target = event.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return
      }

      // Get current state
      const currentState = Option.isSome(stateResult) ? stateResult.value : null
      if (!currentState || !currentCard) return

      // Spacebar toggles show/hide answer
      if (event.code === 'Space' || event.key === ' ') {
        event.preventDefault()
        setShowAnswer({ flashcardGroupId, show: !currentState.showAnswer })
        return
      }

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
    currentCard,
    flashcardGroupId,
    setShowAnswer,
    gotItRight,
    gotItWrong,
  ])

  // Initialize queue when component mounts or group changes
  // Wait a bit to ensure flashcards are loaded first
  useEffect(() => {
    reset({ flashcardGroupId })
    // Small delay to ensure flashcardsAtom has started loading
    const timer = setTimeout(() => {
      initializeQueue({ projectId, flashcardGroupId, includeMastered: false })
    }, 100)
    return () => clearTimeout(timer)
  }, [flashcardGroupId, reset, initializeQueue])

  if (!projectId) return null

  return (
    <div className="flex flex-col flex-1 min-h-0" {...props}>
      <FlashcardContent
        flashcardGroupId={flashcardGroupId}
        projectId={projectId}
        onSubmit={handleSubmitPendingPracticeRecords}
        onRetry={handleRetry}
        onRetryWrong={handleRetryWrong}
        onClose={handleClose}
      />
    </div>
  )
}
