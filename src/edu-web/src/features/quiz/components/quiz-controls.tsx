import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useAtomValue, useAtomSet, Result } from '@effect-atom/atom-react'
import { Option } from 'effect'
import {
  quizDetailStateAtom,
  canSubmitQuizAtom,
  goToNextQuestionAtom,
  goToPreviousQuestionAtom,
  submitQuizAtom,
} from '@/data-acess/quiz-detail-state'
import { quizQuestionsAtom } from '@/data-acess/quiz'

type QuizControlsProps = {
  quizId: string
  projectId: string
}

export const QuizControls = ({ quizId, projectId }: QuizControlsProps) => {
  const stateResult = useAtomValue(quizDetailStateAtom(quizId))
  const questionsResult = useAtomValue(quizQuestionsAtom({ projectId, quizId }))
  const canSubmitResult = useAtomValue(canSubmitQuizAtom({ projectId, quizId }))

  const goToNext = useAtomSet(goToNextQuestionAtom, { mode: 'promise' })
  const goToPrevious = useAtomSet(goToPreviousQuestionAtom, { mode: 'promise' })
  const submitQuiz = useAtomSet(submitQuizAtom, { mode: 'promise' })

  const state = Option.isSome(stateResult) ? stateResult.value : null
  if (!state) return null

  const questions = Result.isSuccess(questionsResult)
    ? questionsResult.value
    : []
  const canSubmit = Result.isSuccess(canSubmitResult)
    ? canSubmitResult.value
    : false

  const currentIndex = state.currentQuestionIndex
  const totalQuestions = questions.length
  const showResults = state.showResults

  const handleNext = async () => {
    await goToNext({ quizId, projectId })
  }

  const handlePrevious = async () => {
    await goToPrevious({ quizId })
  }

  const handleSubmit = async () => {
    await submitQuiz({ quizId, projectId })
  }

  if (showResults) return null

  return (
    <div className="flex items-center justify-center pt-4 pb-4">
      <div className="flex gap-4">
        <Button
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          variant="outline"
          className="flex items-center gap-2"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>

        {currentIndex === totalQuestions - 1 ? (
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            size="lg"
            className="px-8"
          >
            Submit Quiz
          </Button>
        ) : (
          <Button
            onClick={handleNext}
            disabled={!state.selectedByQuestionId[questions[currentIndex]?.id]}
            variant="default"
            className="flex items-center gap-2"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
