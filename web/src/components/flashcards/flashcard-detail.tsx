import { flashcardsAtom } from '@/data-acess/flashcard'
import {
  flashcardDetailStateAtom,
  gotItRightAtom,
  gotItWrongAtom,
  resetAtom,
  setShowAnswerAtom,
  submitPendingAttemptsAtom,
} from '@/data-acess/flashcard-detail-state'
import {
  Result,
  useAtom,
  useAtomSet,
  useAtomValue,
} from '@effect-atom/atom-react'
import React, { useEffect, useCallback, useMemo, useRef } from 'react'
import { Loader2Icon, Upload, RotateCcw, X } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { FlashcardProgress } from './flashcard-progress'
import { FlashcardCard } from './flashcard-card'
import { FlashcardNavigation } from './flashcard-navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Option } from 'effect'
import { currentProjectIdAtom } from '@/data-acess/project'
import { flashcardDetailRoute } from '@/routes/_config'

type Props = React.ComponentProps<'div'> & {
  flashcardGroupId: string
}

export const FlashcardDetail = ({ flashcardGroupId, ...props }: Props) => {
  const navigate = useNavigate()

  const { projectId } = flashcardDetailRoute.useParams()

  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupId))
  const [stateResult] = useAtom(flashcardDetailStateAtom(flashcardGroupId))
  const state = Option.isSome(stateResult) ? stateResult.value : null

  const setShowAnswer = useAtomSet(setShowAnswerAtom)
  const reset = useAtomSet(resetAtom)
  const submitPendingAttempts = useAtomSet(submitPendingAttemptsAtom, {
    mode: 'promise',
  })
  const gotItRight = useAtomSet(gotItRightAtom)
  const gotItWrong = useAtomSet(gotItWrongAtom)

  const stats = useMemo(() => {
    const pendingAttempts = state?.pendingAttempts ?? {}
    const attempts = Object.values(pendingAttempts)
    const total = attempts.length
    const correct = attempts.filter((a) => a.was_correct).length
    const incorrect = attempts.filter((a) => !a.was_correct).length
    const percentage = total > 0 ? Math.round((correct / total) * 100) : 0
    return { total, correct, incorrect, percentage }
  }, [state])

  const toggleAnswer = useCallback(() => {
    const showAnswer = state?.showAnswer ?? false
    setShowAnswer({ flashcardGroupId, show: !showAnswer })
  }, [state?.showAnswer, flashcardGroupId, setShowAnswer])

  const handleClose = useCallback(() => {
    if (!projectId) return

    navigate({
      to: '/projects/$projectId',
      params: { projectId },
    })
  }, [navigate, projectId])

  const handleSubmitPendingAttempts = async () => {
    if (!projectId) return

    await submitPendingAttempts({ flashcardGroupId, projectId })
    handleClose()
  }

  const handleRetry = () => {
    reset({ flashcardGroupId })
  }

  const handleGotItRight = useCallback(() => {
    if (!projectId) return

    gotItRight({ flashcardGroupId, projectId })
  }, [projectId, flashcardGroupId, gotItRight])

  const handleGotItWrong = useCallback(() => {
    if (!projectId) return

    gotItWrong({ flashcardGroupId, projectId })
  }, [projectId, flashcardGroupId, gotItWrong])

  useEffect(() => {
    reset({ flashcardGroupId })
  }, [flashcardGroupId, reset])

  // Keyboard shortcuts: R for right, W for wrong, Space to toggle answer
  useEffect(() => {
    if (!projectId) return

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
          ? flashcardsResult.value.flashcards?.[currentState.currentCardIndex]
          : null

      if (!currentCard) return

      const isCardMarked = currentState.markedCardIds.has(currentCard.id)

      // Spacebar toggles show/hide answer
      if (event.code === 'Space' || event.key === ' ') {
        event.preventDefault()
        toggleAnswer()
        return
      }

      // Only handle right/wrong shortcuts when answer is shown and card is not marked
      if (!currentState.showAnswer || isCardMarked) return

      if (event.key === 'r' || event.key === 'R') {
        event.preventDefault()
        handleGotItRight()
      } else if (event.key === 'w' || event.key === 'W') {
        event.preventDefault()
        handleGotItWrong()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [
    projectId,
    stateResult,
    flashcardsResult,
    toggleAnswer,
    handleGotItRight,
    handleGotItWrong,
  ])

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

          const hasPendingAttempts =
            Object.keys(state.pendingAttempts).length > 0
          const allCardsMarked = state.markedCardIds.size === flashcards.length

          if (state.isCompleted || allCardsMarked) {
            return (
              <div className="flex flex-col items-center justify-center flex-1 min-h-0 overflow-auto p-4">
                <Card className="w-full max-w-2xl">
                  <CardHeader>
                    <CardTitle className="text-2xl text-center">
                      Flashcard Session Complete!
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="space-y-2">
                        <div className="text-3xl font-bold text-green-600">
                          {stats.correct}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Correct
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="text-3xl font-bold text-red-600">
                          {stats.incorrect}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Incorrect
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="text-3xl font-bold text-blue-600">
                          {stats.percentage}%
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Success Rate
                        </div>
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <div className="text-center text-sm text-muted-foreground mb-4">
                        Total: {stats.total} flashcards
                      </div>
                    </div>

                    <div className="flex flex-col gap-3">
                      <Button
                        onClick={handleSubmitPendingAttempts}
                        disabled={!hasPendingAttempts}
                        variant="default"
                        className="w-full flex items-center justify-center gap-2"
                        size="lg"
                      >
                        <Upload className="h-4 w-4" />
                        Submit Attempts ({stats.total})
                      </Button>

                      <div className="flex gap-3">
                        <Button
                          onClick={handleRetry}
                          variant="outline"
                          className="flex-1 flex items-center justify-center gap-2"
                        >
                          <RotateCcw className="h-4 w-4" />
                          Retry
                        </Button>
                        <Button
                          onClick={handleClose}
                          variant="outline"
                          className="flex-1 flex items-center justify-center gap-2"
                        >
                          <X className="h-4 w-4" />
                          Close
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )
          }

          return (
            <div className="flex flex-col space-y-12 flex-1 min-h-0 overflow-auto p-4">
              <FlashcardProgress
                currentIndex={state.currentCardIndex}
                totalCount={flashcards.length}
              />

              <FlashcardCard
                question={currentCard.question}
                answer={currentCard.answer}
                showAnswer={state.showAnswer}
                onToggle={toggleAnswer}
              />

              <FlashcardNavigation
                showAnswer={state.showAnswer}
                isCardMarked={state.markedCardIds.has(currentCard.id)}
                onToggleAnswer={toggleAnswer}
                onGotItRight={handleGotItRight}
                onGotItWrong={handleGotItWrong}
              />
            </div>
          )
        })
        .render()}
    </div>
  )
}
