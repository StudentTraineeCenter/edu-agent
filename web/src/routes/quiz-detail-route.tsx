import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Skeleton } from '@/components/ui/skeleton'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { quizAtom, quizQuestionsAtom } from '@/data-acess/quiz'
import { quizDetailRoute } from '@/routes/_config'
import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle } from 'lucide-react'

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

export const QuizDetailPage = () => {
  const { quizId } = quizDetailRoute.useParams()
  const quizResult = useAtomValue(quizAtom(quizId))
  const questionsResult = useAtomValue(quizQuestionsAtom(quizId))
  const [selectedByQuestionId, setSelectedByQuestionId] = useState<
    Record<string, 'A' | 'B' | 'C' | 'D'>
  >({})
  const [showResults, setShowResults] = useState(false)

  const correctCount = useMemo(() => {
    if (!showResults) return 0
    return Result.match(questionsResult, {
      onSuccess: (res) =>
        res.value.quiz_questions.reduce((acc, q) => {
          return (
            acc +
            (selectedByQuestionId[q.id] === (q.correct_option as any) ? 1 : 0)
          )
        }, 0),
      onFailure: () => 0,
      onInitial: () => 0,
    })
  }, [questionsResult, selectedByQuestionId, showResults])

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
                <span>Loading questions...</span>
              </div>
            ))
            .onFailure(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
                <span>Failed to load questions</span>
              </div>
            ))
            .onSuccess((res) => (
              <div className="flex flex-col gap-6 p-4">
                <div className="text-center">
                  {Result.builder(quizResult)
                    .onSuccess((qr) => (
                      <>
                        <h1 className="text-2xl font-bold">
                          {qr.quiz?.name || 'Quiz'}
                        </h1>
                        <p className="text-muted-foreground">
                          {res.quiz_questions.length} questions
                        </p>
                        {showResults && (
                          <p className="text-lg font-semibold mt-2">
                            Score: {correctCount}/{res.quiz_questions.length} (
                            {res.quiz_questions.length > 0
                              ? Math.round(
                                  (correctCount / res.quiz_questions.length) *
                                    100,
                                )
                              : 0}
                            %)
                          </p>
                        )}
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
                  res.quiz_questions.map((q, idx) => {
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
                          ? 'bg-blue-100 border-blue-500'
                          : 'bg-white border-gray-200'
                      }
                      const isSelected = selected === option
                      const isCorrect = q.correct_option === option
                      if (isCorrect)
                        return 'bg-green-100 border-green-500 text-green-800'
                      if (isSelected && !isCorrect)
                        return 'bg-red-100 border-red-500 text-red-800'
                      return 'bg-gray-50 border-gray-200'
                    }

                    return (
                      <div
                        key={q.id}
                        className="bg-white border rounded-lg p-4 shadow-sm"
                      >
                        <div className="space-y-3">
                          <div className="flex items-start gap-3">
                            <span className="font-bold text-lg text-muted-foreground">
                              {idx + 1}.
                            </span>
                            <h3 className="text-lg font-medium leading-relaxed flex-1">
                              {q.question_text}
                            </h3>
                            {showResults && (
                              <div className="ml-auto">
                                {selected === q.correct_option ? (
                                  <CheckCircle className="h-5 w-5 text-green-600" />
                                ) : (
                                  <XCircle className="h-5 w-5 text-red-600" />
                                )}
                              </div>
                            )}
                          </div>

                          <div className="grid gap-2 pl-8">
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
                                className={`text-left p-3 border rounded-lg transition-colors hover:bg-gray-50 ${getAnswerClasses(opt.key)} ${showResults ? 'cursor-default' : 'cursor-pointer'}`}
                              >
                                <div className="flex gap-3">
                                  <span className="font-semibold">
                                    {opt.key}.
                                  </span>
                                  <span>{opt.label}</span>
                                </div>
                              </button>
                            ))}
                          </div>

                          {showResults && (
                            <div className="pl-8 pt-1 text-sm text-muted-foreground">
                              Correct answer:{' '}
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
                              {q.explanation ? (
                                <div className="mt-1 text-xs text-muted-foreground">
                                  {q.explanation}
                                </div>
                              ) : null}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}

                {!showResults && res.quiz_questions.length > 0 && (
                  <div className="flex justify-center pt-2">
                    <Button
                      onClick={() => setShowResults(true)}
                      disabled={
                        Object.keys(selectedByQuestionId).length !==
                        res.quiz_questions.length
                      }
                      className="px-8 py-3 text-lg"
                    >
                      Submit
                    </Button>
                  </div>
                )}

                {showResults && (
                  <div className="flex justify-center gap-4 pt-2">
                    <Button
                      onClick={() => {
                        setSelectedByQuestionId({})
                        setShowResults(false)
                      }}
                      variant="outline"
                      className="px-6 py-3"
                    >
                      Restart
                    </Button>
                  </div>
                )}
              </div>
            ))
            .render()}
        </div>
      </div>
    </div>
  )
}
