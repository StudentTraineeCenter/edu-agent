import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Skeleton } from '@/components/ui/skeleton'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { quizAtom, quizQuestionsAtom } from '@/data-acess/quiz'
import { submitAttemptsBatchAtom } from '@/data-acess/attempt'
import { quizDetailRoute } from '@/routes/_config'
import { useState, useMemo, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import {
  CheckCircle,
  XCircle,
  Upload,
  RotateCcw,
  X,
  Loader2Icon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import type { CreateAttemptRequest } from '@/integrations/api'
import { useNavigate } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

const QuizHeader = ({ title }: { title?: string }) => (
  <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
    <div className="flex flex-1 items-center gap-2 px-3">
      <SidebarTrigger />
      <Separator
        orientation="vertical"
        className="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {title}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  </header>
)

const extractTopic = (text: string, maxLength = 100): string => {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

export const QuizDetailPage = () => {
  const { quizId, projectId } = quizDetailRoute.useParams()
  const quizResult = useAtomValue(quizAtom(quizId))
  const questionsResult = useAtomValue(quizQuestionsAtom(quizId))
  const [selectedByQuestionId, setSelectedByQuestionId] = useState<
    Record<string, 'A' | 'B' | 'C' | 'D'>
  >({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [pendingMistakes, setPendingMistakes] = useState<
    Record<string, CreateAttemptRequest>
  >({})
  const submitAttemptsBatch = useAtomSet(submitAttemptsBatchAtom, {
    mode: 'promise',
  })

  const navigate = useNavigate()

  const stats = useMemo(() => {
    if (!showResults)
      return { total: 0, correct: 0, incorrect: 0, percentage: 0 }
    return Result.match(questionsResult, {
      onSuccess: (res) => {
        const total = res.value.quiz_questions.length
        const correct = res.value.quiz_questions.reduce((acc, q) => {
          return (
            acc +
            (selectedByQuestionId[q.id] === (q.correct_option as any) ? 1 : 0)
          )
        }, 0)
        const incorrect = total - correct
        const percentage = total > 0 ? Math.round((correct / total) * 100) : 0
        return { total, correct, incorrect, percentage }
      },
      onFailure: () => ({ total: 0, correct: 0, incorrect: 0, percentage: 0 }),
      onInitial: () => ({ total: 0, correct: 0, incorrect: 0, percentage: 0 }),
    })
  }, [questionsResult, selectedByQuestionId, showResults])

  const handleSubmitQuiz = useCallback(() => {
    setShowResults(true)

    // Track mistakes (only incorrect answers)
    if (questionsResult._tag !== 'Success') return

    const mistakes: Record<string, CreateAttemptRequest> = {}
    const questions = questionsResult.value.quiz_questions

    questions.forEach((q) => {
      const userAnswer = selectedByQuestionId[q.id]
      const correctOption = q.correct_option

      // Only track mistakes (incorrect answers)
      if (userAnswer && userAnswer !== correctOption) {
        mistakes[q.id] = {
          item_type: 'quiz',
          item_id: q.id,
          topic: extractTopic(q.question_text),
          user_answer: userAnswer,
          correct_answer: correctOption,
          was_correct: false,
        }
      }
    })

    setPendingMistakes(mistakes)
  }, [questionsResult, selectedByQuestionId])

  const submitPendingMistakes = useCallback(async () => {
    const mistakesArray = Object.values(pendingMistakes)
    if (mistakesArray.length === 0) return

    try {
      await submitAttemptsBatch({
        projectId,
        attempts: mistakesArray as unknown as [
          CreateAttemptRequest,
          ...CreateAttemptRequest[],
        ],
      })
      setPendingMistakes({})
    } catch (error) {
      console.error('Failed to submit mistakes:', error)
      throw error
    }
  }, [pendingMistakes, projectId, submitAttemptsBatch])

  const handleRetry = () => {
    setSelectedByQuestionId({})
    setCurrentQuestionIndex(0)
    setShowResults(false)
    setPendingMistakes({})
  }

  const handleNext = useCallback(() => {
    setCurrentQuestionIndex((prev) => prev + 1)
  }, [])

  const handlePrevious = useCallback(() => {
    setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))
  }, [])

  const handleClose = () => {
    navigate({
      to: '/projects/$projectId',
      params: { projectId },
    })
  }

  return (
    <div className="flex h-full flex-col">
      {Result.builder(quizResult)
        .onSuccess((res) => <QuizHeader title={res.quiz?.name || 'Quiz'} />)
        .onInitialOrWaiting(() => (
          <div className="h-14 shrink-0">
            <Skeleton className="w-72 h-7 mt-3 ml-4" />
          </div>
        ))
        .onFailure(() => <QuizHeader title="Quiz" />)
        .render()}

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="max-w-5xl mx-auto w-full flex flex-col flex-1 min-h-0 overflow-auto">
          {Result.builder(questionsResult)
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
            .onSuccess((res) => {
              if (showResults) {
                return (
                  <div className="flex flex-col items-center justify-center flex-1 min-h-0 overflow-auto p-4">
                    <Card className="w-full max-w-2xl">
                      <CardHeader>
                        <CardTitle className="text-2xl text-center">
                          Quiz Complete!
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
                            Total: {stats.total} questions
                          </div>
                        </div>

                        <div className="border-t pt-4 space-y-3">
                          <h3 className="text-sm font-semibold">
                            Review Answers
                          </h3>
                          <div className="space-y-2 max-h-96 overflow-auto">
                            {res.quiz_questions.map((q, idx) => {
                              const userAnswer = selectedByQuestionId[q.id]
                              const isCorrect = userAnswer === q.correct_option
                              const getOptionText = (option: string) => {
                                if (option === 'A') return q.option_a
                                if (option === 'B') return q.option_b
                                if (option === 'C') return q.option_c
                                return q.option_d
                              }

                              return (
                                <div
                                  key={q.id}
                                  className="border-b pb-3 last:border-0 last:pb-0"
                                >
                                  <div className="flex items-start gap-2">
                                    <div className="flex items-center gap-2 shrink-0 mt-0.5">
                                      {isCorrect ? (
                                        <CheckCircle className="h-4 w-4 text-green-600" />
                                      ) : (
                                        <XCircle className="h-4 w-4 text-red-600" />
                                      )}
                                      <span className="text-xs font-medium text-muted-foreground w-6">
                                        {idx + 1}
                                      </span>
                                    </div>
                                    <div className="flex-1 space-y-1.5 min-w-0">
                                      <p className="text-sm leading-relaxed">
                                        {q.question_text}
                                      </p>
                                      <div className="flex flex-wrap items-center gap-3 text-xs">
                                        <div className="flex items-center gap-1.5">
                                          <span className="text-muted-foreground">
                                            You:
                                          </span>
                                          <span
                                            className={`font-medium ${
                                              isCorrect
                                                ? 'text-green-600'
                                                : 'text-red-600'
                                            }`}
                                          >
                                            {userAnswer?.toUpperCase() ||
                                              'No answer'}
                                            {userAnswer &&
                                              ` - ${getOptionText(userAnswer)}`}
                                          </span>
                                        </div>
                                        {!isCorrect && (
                                          <>
                                            <span className="text-muted-foreground">
                                              •
                                            </span>
                                            <div className="flex items-center gap-1.5">
                                              <span className="text-muted-foreground">
                                                Correct:
                                              </span>
                                              <span className="font-medium text-green-700">
                                                {q.correct_option.toUpperCase()}{' '}
                                                -{' '}
                                                {getOptionText(
                                                  q.correct_option,
                                                )}
                                              </span>
                                            </div>
                                          </>
                                        )}
                                      </div>
                                      {q.explanation && (
                                        <div className="text-xs text-muted-foreground italic">
                                          {q.explanation}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>

                        <div className="flex flex-col gap-3">
                          {Object.keys(pendingMistakes).length > 0 && (
                            <Button
                              onClick={submitPendingMistakes}
                              variant="default"
                              className="w-full flex items-center justify-center gap-2"
                              size="lg"
                            >
                              <Upload className="h-4 w-4" />
                              Submit Mistakes (
                              {Object.keys(pendingMistakes).length})
                            </Button>
                          )}

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
                  <div className="text-center space-y-2">
                    {Result.builder(quizResult)
                      .onSuccess((qr) => (
                        <>
                          <h1 className="text-2xl font-bold">
                            {qr.quiz?.name || 'Quiz'}
                          </h1>
                          <p className="text-muted-foreground">
                            {res.quiz_questions.length} questions
                          </p>
                        </>
                      ))
                      .onInitialOrWaiting(() => <div className="h-7" />)
                      .onFailure(() => <div className="h-7" />)
                      .render()}
                  </div>

                  {res.quiz_questions.length === 0 ? (
                    <div className="flex flex-1 items-center justify-center text-muted-foreground">
                      No questions
                    </div>
                  ) : (
                    <>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                          <span>
                            Question {currentQuestionIndex + 1} of{' '}
                            {res.quiz_questions.length}
                          </span>
                          <span>
                            {Math.round(
                              ((currentQuestionIndex + 1) /
                                res.quiz_questions.length) *
                                100,
                            )}
                            % complete
                          </span>
                        </div>
                        <Progress
                          value={
                            ((currentQuestionIndex + 1) /
                              res.quiz_questions.length) *
                            100
                          }
                          className="h-2"
                        />
                      </div>

                      <div className="flex-1 flex items-center justify-center">
                        <div className="w-full max-w-3xl">
                          {(() => {
                            const q = res.quiz_questions[currentQuestionIndex]
                            const selected = selectedByQuestionId[q.id]
                            const options: Array<{
                              key: 'A' | 'B' | 'C' | 'D'
                              label: string
                            }> = [
                              { key: 'A', label: q.option_a },
                              { key: 'B', label: q.option_b },
                              { key: 'C', label: q.option_c },
                              { key: 'D', label: q.option_d },
                            ]

                            const getAnswerClasses = (
                              option: 'A' | 'B' | 'C' | 'D',
                            ) => {
                              if (!showResults) {
                                return selected === option
                                  ? 'bg-primary/10 border-primary'
                                  : 'bg-card border-border'
                              }
                              const isSelected = selected === option
                              const isCorrect = q.correct_option === option
                              if (isCorrect)
                                return 'bg-green-50 border-green-500 text-green-900'
                              if (isSelected && !isCorrect)
                                return 'bg-red-50 border-red-500 text-red-900'
                              return 'bg-muted/50 border-border'
                            }

                            return (
                              <div className="bg-card border rounded-xl shadow-lg p-12">
                                <div className="space-y-10">
                                  <div>
                                    <h3 className="text-lg font-medium leading-relaxed mb-6">
                                      {q.question_text}
                                    </h3>
                                    {showResults && (
                                      <div className="flex items-center gap-2 mb-4">
                                        {selected === q.correct_option ? (
                                          <>
                                            <CheckCircle className="h-5 w-5 text-green-600 shrink-0" />
                                            <span className="text-sm text-green-600 font-medium">
                                              Correct
                                            </span>
                                          </>
                                        ) : (
                                          <>
                                            <XCircle className="h-5 w-5 text-red-600 shrink-0" />
                                            <span className="text-sm text-red-600 font-medium">
                                              Incorrect
                                            </span>
                                          </>
                                        )}
                                      </div>
                                    )}
                                  </div>

                                  <div className="grid gap-3">
                                    {options.map((opt) => (
                                      <button
                                        key={opt.key}
                                        onClick={() => {
                                          if (showResults) return
                                          setSelectedByQuestionId((prev) => ({
                                            ...prev,
                                            [q.id]: opt.key,
                                          }))
                                        }}
                                        disabled={showResults}
                                        className={`text-left p-4 border rounded-lg transition-all ${
                                          showResults
                                            ? 'cursor-default'
                                            : 'cursor-pointer hover:shadow-md'
                                        } ${getAnswerClasses(opt.key)}`}
                                      >
                                        <div className="flex gap-3">
                                          <span className="font-semibold shrink-0">
                                            {opt.key}.
                                          </span>
                                          <span className="leading-relaxed">
                                            {opt.label}
                                          </span>
                                        </div>
                                      </button>
                                    ))}
                                  </div>

                                  {showResults && (
                                    <div className="pt-4 space-y-2 border-t">
                                      <div className="text-sm">
                                        <span className="text-muted-foreground">
                                          Correct answer:{' '}
                                        </span>
                                        <span className="font-semibold text-green-700">
                                          {q.correct_option}.{' '}
                                          {q.correct_option === 'A'
                                            ? q.option_a
                                            : q.correct_option === 'B'
                                              ? q.option_b
                                              : q.correct_option === 'C'
                                                ? q.option_c
                                                : q.option_d}
                                        </span>
                                      </div>
                                      {q.explanation && (
                                        <div className="text-sm text-muted-foreground leading-relaxed">
                                          <span className="font-medium">
                                            Explanation:{' '}
                                          </span>
                                          {q.explanation}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )
                          })()}
                        </div>
                      </div>

                      {!showResults && (
                        <div className="flex items-center justify-center gap-4 pt-4">
                          <Button
                            onClick={handlePrevious}
                            disabled={currentQuestionIndex === 0}
                            variant="outline"
                            className="flex items-center gap-2"
                          >
                            <ChevronLeft className="h-4 w-4" />
                            Previous
                          </Button>

                          {currentQuestionIndex ===
                          res.quiz_questions.length - 1 ? (
                            <Button
                              onClick={handleSubmitQuiz}
                              disabled={
                                Object.keys(selectedByQuestionId).length !==
                                res.quiz_questions.length
                              }
                              size="lg"
                              className="px-8"
                            >
                              Submit Quiz
                            </Button>
                          ) : (
                            <Button
                              onClick={handleNext}
                              disabled={
                                !selectedByQuestionId[
                                  res.quiz_questions[currentQuestionIndex].id
                                ]
                              }
                              variant="default"
                              className="flex items-center gap-2"
                            >
                              Next
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )
            })
            .render()}
        </div>
      </div>
    </div>
  )
}
