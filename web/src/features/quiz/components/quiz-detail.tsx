import {
  quizDetailStateAtom,
  resetQuizAtom,
  setSelectedAnswerAtom,
  goToNextQuestionAtom,
  goToPreviousQuestionAtom,
  submitQuizAtom,
} from '@/data-acess/quiz-detail-state'
import { quizQuestionsAtom } from '@/data-acess/quiz'
import { useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import React, { useEffect } from 'react'
import { Option } from 'effect'
import { QuizContent } from './quiz-content'

type Props = React.ComponentProps<'div'> & {
  quizId: string
  projectId: string
}

export const QuizDetail = ({ quizId, projectId, ...props }: Props) => {
  const questionsResult = useAtomValue(quizQuestionsAtom(quizId))
  const stateResult = useAtomValue(quizDetailStateAtom(quizId))

  const resetQuiz = useAtomSet(resetQuizAtom)
  const setSelectedAnswer = useAtomSet(setSelectedAnswerAtom, {
    mode: 'promise',
  })
  const goToNext = useAtomSet(goToNextQuestionAtom, { mode: 'promise' })
  const goToPrevious = useAtomSet(goToPreviousQuestionAtom, { mode: 'promise' })
  const submitQuiz = useAtomSet(submitQuizAtom, { mode: 'promise' })

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input/textarea
      const target = event.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return
      }

      const state = Option.isSome(stateResult) ? stateResult.value : null
      if (!state) return

      // Don't handle shortcuts when showing results
      if (state.showResults) return

      const questions =
        questionsResult._tag === 'Success' ? questionsResult.value : null
      if (!questions) return

      const currentQuestion = questions[state.currentQuestionIndex]
      if (!currentQuestion) return

      // Arrow keys for navigation
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault()
        if (event.key === 'ArrowLeft') {
          goToPrevious({ quizId })
        } else {
          goToNext({ quizId })
        }
        return
      }

      // Number keys for selecting answers (1-4 for A-D)
      if (event.key >= '1' && event.key <= '4') {
        event.preventDefault()
        const option = ['A', 'B', 'C', 'D'][parseInt(event.key) - 1] as
          | 'A'
          | 'B'
          | 'C'
          | 'D'
        setSelectedAnswer({
          quizId,
          questionId: currentQuestion.id,
          option,
        })
        return
      }

      // Enter to submit if on last question and all answered
      if (event.key === 'Enter') {
        const allAnswered =
          Object.keys(state.selectedByQuestionId).length === questions.length
        const isLastQuestion =
          state.currentQuestionIndex === questions.length - 1
        if (allAnswered && isLastQuestion) {
          event.preventDefault()
          submitQuiz({ quizId })
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [
    quizId,
    stateResult,
    questionsResult,
    setSelectedAnswer,
    goToNext,
    goToPrevious,
    submitQuiz,
  ])

  useEffect(() => {
    resetQuiz({ quizId })
  }, [quizId, resetQuiz])

  return (
    <div className="flex flex-col flex-1 min-h-0" {...props}>
      <QuizContent quizId={quizId} projectId={projectId} />
    </div>
  )
}
