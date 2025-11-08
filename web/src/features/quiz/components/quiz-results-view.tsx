import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  CheckCircle,
  XCircle,
  Upload,
  RotateCcw,
  X,
  Trophy,
  ChevronDown,
} from 'lucide-react'
import { useState, useMemo } from 'react'
import { useNavigate } from '@tanstack/react-router'
import type { QuizQuestionDto } from '@/integrations/api/client'
import { Result, useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { Option } from 'effect'
import {
  quizDetailStateAtom,
  quizStatsAtom,
  resetQuizAtom,
  submitPendingMistakesAtom,
} from '@/data-acess/quiz-detail-state'
import { quizQuestionsAtom } from '@/data-acess/quiz'

const getOptionText = (
  question: QuizQuestionDto,
  option: 'A' | 'B' | 'C' | 'D',
) => {
  if (option === 'A') return question.option_a
  if (option === 'B') return question.option_b
  if (option === 'C') return question.option_c
  return question.option_d
}

type CompletionHeaderProps = {
  total: number
}

const CompletionHeader = ({ total }: CompletionHeaderProps) => (
  <div className="text-center space-y-2">
    <div className="flex items-center justify-center gap-2 mb-2">
      <Trophy className="h-8 w-8 text-yellow-500" />
      <h2 className="text-3xl font-bold">Quiz Complete!</h2>
    </div>
    <p className="text-muted-foreground">
      You've completed all {total} questions
    </p>
  </div>
)

type StatCardProps = {
  icon?: React.ReactNode
  value: string | number
  label: string
  valueColor?: string
}

const StatCard = ({ icon, value, label, valueColor }: StatCardProps) => (
  <div className="flex flex-col items-center space-y-3 p-6 rounded-lg border bg-card">
    <div className={`flex items-center ${icon ? 'gap-2' : ''}`}>
      {icon}
      <div className={`text-4xl font-bold ${valueColor || ''}`}>{value}</div>
    </div>
    <div className="text-sm font-medium text-muted-foreground">{label}</div>
  </div>
)

const StatsGrid = ({ quizId }: { quizId: string }) => {
  const statsResult = useAtomValue(quizStatsAtom(quizId))

  return Result.builder(statsResult)
    .onSuccess((stats) => {
      return (
        <div className="grid grid-cols-3 gap-6">
          <StatCard
            icon={<CheckCircle className="h-6 w-6 text-green-600" />}
            value={stats.correct}
            label="Correct"
            valueColor="text-green-600"
          />
          <StatCard
            icon={<XCircle className="h-6 w-6 text-red-600" />}
            value={stats.incorrect}
            label="Incorrect"
            valueColor="text-red-600"
          />
          <StatCard
            icon={null}
            value={`${stats.percentage}%`}
            label="Success Rate"
            valueColor="text-blue-600"
          />
        </div>
      )
    })
    .render()
}

type QuizQuestionListItemProps = {
  question: QuizQuestionDto
  index: number
  userAnswer?: 'A' | 'B' | 'C' | 'D'
  isCorrect: boolean
}

const QuizQuestionListItem = ({
  question,
  index,
  userAnswer,
  isCorrect,
}: QuizQuestionListItemProps) => (
  <div className="border-b last:border-0 pb-3 last:pb-0 space-y-2">
    <div className="flex items-start gap-2">
      <span className="text-xs font-medium text-muted-foreground w-6 shrink-0">
        {index + 1}
      </span>
      <div className="flex-1 space-y-1.5 min-w-0">
        <p className="text-sm font-medium leading-relaxed">
          {question.question_text}
        </p>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-muted-foreground">You:</span>
            <span
              className={`font-medium ${
                isCorrect ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {userAnswer?.toUpperCase() || 'No answer'}
              {userAnswer && ` - ${getOptionText(question, userAnswer)}`}
            </span>
          </div>
          {!isCorrect && (
            <>
              <span className="text-muted-foreground">•</span>
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground">Correct:</span>
                <span className="font-medium text-green-700">
                  {question.correct_option.toUpperCase()} -{' '}
                  {getOptionText(
                    question,
                    question.correct_option as 'A' | 'B' | 'C' | 'D',
                  )}
                </span>
              </div>
            </>
          )}
        </div>
        {question.explanation && (
          <div className="text-xs text-muted-foreground italic leading-relaxed">
            {question.explanation}
          </div>
        )}
      </div>
    </div>
  </div>
)

type QuizReviewSectionProps = {
  title: string
  questions: Array<{
    question: QuizQuestionDto
    index: number
    userAnswer?: 'A' | 'B' | 'C' | 'D'
  }>
  icon: React.ReactNode
  isOpen: boolean
  onOpenChange: (open: boolean) => void
}

const QuizReviewSection = ({
  title,
  questions,
  icon,
  isOpen,
  onOpenChange,
}: QuizReviewSectionProps) => {
  if (questions.length === 0) return null

  return (
    <Collapsible open={isOpen} onOpenChange={onOpenChange}>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border bg-card p-4 hover:bg-accent transition-colors">
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-semibold">
            {title} ({questions.length})
          </span>
        </div>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-2">
        <div className="rounded-lg border bg-muted/50 p-4 space-y-3">
          {questions.map(({ question, index, userAnswer }) => {
            const isCorrect = userAnswer === question.correct_option
            return (
              <QuizQuestionListItem
                key={question.id}
                question={question}
                index={index}
                userAnswer={userAnswer}
                isCorrect={isCorrect}
              />
            )
          })}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

type CompletionActionsProps = {
  quizId: string
  projectId: string
}

const CompletionActions = ({ quizId, projectId }: CompletionActionsProps) => {
  const navigate = useNavigate()

  const stateResult = useAtomValue(quizDetailStateAtom(quizId))
  const resetQuiz = useAtomSet(resetQuizAtom)
  const submitPendingMistakes = useAtomSet(submitPendingMistakesAtom, {
    mode: 'promise',
  })

  const hasPendingMistakes =
    Option.isSome(stateResult) &&
    Object.keys(stateResult.value.pendingMistakes).length > 0

  const handleSubmit = async () => {
    await submitPendingMistakes({ quizId, projectId })
    navigate({
      to: '/p/$projectId',
      params: { projectId },
    })
  }

  const handleRetry = () => {
    resetQuiz({ quizId })
  }

  const handleClose = () => {
    navigate({
      to: '/p/$projectId',
      params: { projectId },
    })
  }

  return (
    <div className="flex flex-col gap-3">
      {hasPendingMistakes && (
        <Button
          onClick={handleSubmit}
          variant="default"
          className="w-full flex items-center justify-center gap-2"
          size="lg"
        >
          <Upload className="h-4 w-4" />
          Submit Mistakes (
          {Object.keys(stateResult.value.pendingMistakes).length})
        </Button>
      )}

      <div className="flex gap-3">
        <Button
          onClick={handleRetry}
          variant="outline"
          className="flex-1 flex items-center justify-center gap-2"
          size="lg"
        >
          <RotateCcw className="h-4 w-4" />
          Retry
        </Button>
        <Button
          onClick={handleClose}
          variant="outline"
          className="flex-1 flex items-center justify-center gap-2"
          size="lg"
        >
          <X className="h-4 w-4" />
          Close
        </Button>
      </div>
    </div>
  )
}

type QuizResultsViewProps = {
  quizId: string
  projectId: string
}

export const QuizResultsView = ({
  quizId,
  projectId,
}: QuizResultsViewProps) => {
  const [showCorrect, setShowCorrect] = useState(false)
  const [showIncorrect, setShowIncorrect] = useState(false)

  const stateResult = useAtomValue(quizDetailStateAtom(quizId))
  const statsResult = useAtomValue(quizStatsAtom(quizId))
  const questionsResult = useAtomValue(quizQuestionsAtom(quizId))

  const state = Option.isSome(stateResult) ? stateResult.value : null
  if (!state) return null

  const questions = Result.isSuccess(questionsResult)
    ? questionsResult.value
    : []

  const { correct, incorrect } = useMemo(() => {
    const correctQuestions: Array<{
      question: QuizQuestionDto
      index: number
      userAnswer?: 'A' | 'B' | 'C' | 'D'
    }> = []
    const incorrectQuestions: Array<{
      question: QuizQuestionDto
      index: number
      userAnswer?: 'A' | 'B' | 'C' | 'D'
    }> = []

    questions.forEach((q, idx) => {
      const userAnswer = state.selectedByQuestionId[q.id]
      const isCorrect = userAnswer === q.correct_option

      const item = {
        question: q,
        index: idx,
        userAnswer,
      }

      if (isCorrect) {
        correctQuestions.push(item)
      } else {
        incorrectQuestions.push(item)
      }
    })

    return { correct: correctQuestions, incorrect: incorrectQuestions }
  }, [questions, state.selectedByQuestionId])

  const total = questions.length

  return Result.builder(statsResult)
    .onSuccess(() => (
      <div className="flex flex-col flex-1 min-h-0 overflow-auto p-4">
        <div className="max-w-3xl mx-auto w-full space-y-8 py-8">
          <CompletionHeader total={total} />

          <StatsGrid quizId={quizId} />

          <Separator />

          <div className="space-y-4">
            <QuizReviewSection
              title="Correct Answers"
              questions={correct}
              icon={<CheckCircle className="h-5 w-5 text-green-600" />}
              isOpen={showCorrect}
              onOpenChange={setShowCorrect}
            />

            <QuizReviewSection
              title="Incorrect Answers"
              questions={incorrect}
              icon={<XCircle className="h-5 w-5 text-red-600" />}
              isOpen={showIncorrect}
              onOpenChange={setShowIncorrect}
            />
          </div>

          <Separator />

          <CompletionActions quizId={quizId} projectId={projectId} />
        </div>
      </div>
    ))
    .render()
}
