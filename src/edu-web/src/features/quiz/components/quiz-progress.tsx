import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Option } from 'effect'
import { useMemo } from 'react'
import { Progress } from '@/components/ui/progress'
import { quizDetailStateAtom } from '@/data-acess/quiz-detail-state'
import { quizQuestionsAtom } from '@/data-acess/quiz'

type QuizProgressProps = {
  quizId: string
  projectId: string
}

export const QuizProgress = ({ quizId, projectId }: QuizProgressProps) => {
  const stateResult = useAtomValue(quizDetailStateAtom(quizId))
  const questionsResult = useAtomValue(quizQuestionsAtom({ projectId, quizId }))

  const currentQuestionIdx = Option.isSome(stateResult)
    ? stateResult.value.currentQuestionIndex
    : 0

  const totalCount = useMemo(() => {
    if (!Result.isSuccess(questionsResult)) return 0
    return questionsResult.value.length
  }, [questionsResult])

  const progressPercentage = useMemo(() => {
    if (Option.isNone(stateResult) || !totalCount) return 0

    const { currentQuestionIndex } = stateResult.value

    return ((currentQuestionIndex + 1) / totalCount) * 100
  }, [totalCount, stateResult])

  return (
    <>
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Question {currentQuestionIdx + 1} of {totalCount}
        </span>
        <span>{Math.round(progressPercentage)}% complete</span>
      </div>

      <Progress value={progressPercentage} className="h-2" />
    </>
  )
}
