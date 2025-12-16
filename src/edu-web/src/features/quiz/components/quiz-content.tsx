import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Loader2Icon } from 'lucide-react'
import { Option } from 'effect'
import { QuizResultsView } from './quiz-results-view'
import { QuizProgress } from './quiz-progress'
import { QuizQuestionCard } from './quiz-question-card'
import { QuizControls } from './quiz-controls'
import { quizDetailStateAtom } from '@/data-acess/quiz-detail-state'
import { quizQuestionsAtom } from '@/data-acess/quiz'

type QuizContentProps = {
  quizId: string
  projectId: string
}

export const QuizContent = ({ quizId, projectId }: QuizContentProps) => {
  const questionsResult = useAtomValue(quizQuestionsAtom({ projectId, quizId }))
  const stateResult = useAtomValue(quizDetailStateAtom(quizId))

  return Result.builder(questionsResult)
    .onInitialOrWaiting(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading questions...</span>
      </div>
    ))
    .onFailure(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
        <span>Failed to load questions</span>
      </div>
    ))
    .onSuccess((quizQuestions) => {
      const state = Option.isSome(stateResult) ? stateResult.value : null
      if (!state) return null

      if (quizQuestions.length === 0) {
        return (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            No questions
          </div>
        )
      }

      if (state.showResults) {
        return <QuizResultsView quizId={quizId} projectId={projectId} />
      }

      return (
        <div className="flex flex-col space-y-12 flex-1 min-h-0 overflow-auto p-4">
          <QuizProgress quizId={quizId} projectId={projectId} />

          <QuizQuestionCard quizId={quizId} projectId={projectId} />

          <QuizControls quizId={quizId} projectId={projectId} />
        </div>
      )
    })
    .render()
}
