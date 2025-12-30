import {
  currentQuestionAtom,
  quizDetailStateAtom,
  setSelectedAnswerAtom,
} from '@/data-acess/quiz-detail-state'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { Option } from 'effect'
import { CheckCircle, XCircle } from 'lucide-react'

type QuizQuestionCardProps = {
  quizId: string
  projectId: string
}

export const QuizQuestionCard = ({
  quizId,
  projectId,
}: QuizQuestionCardProps) => {
  const stateResult = useAtomValue(quizDetailStateAtom(quizId))
  const currentQuestionResult = useAtomValue(
    currentQuestionAtom(`${projectId}:${quizId}`),
  )

  const setSelectedAnswer = useAtomSet(setSelectedAnswerAtom, {
    mode: 'promise',
  })

  const state = Option.isSome(stateResult) ? stateResult.value : null
  if (!state) return null

  const currentQuestion = Result.isSuccess(currentQuestionResult)
    ? currentQuestionResult.value
    : null
  if (!currentQuestion) return null

  const selected = state.selectedByQuestionId[currentQuestion.id]
  const showResults = state.showResults

  const handleSelect = async (option: 'A' | 'B' | 'C' | 'D') => {
    if (showResults) return
    await setSelectedAnswer({
      quizId,
      questionId: currentQuestion.id,
      option,
    })
  }

  const options: Array<{
    key: 'A' | 'B' | 'C' | 'D'
    label: string
  }> = [
    { key: 'A', label: currentQuestion.option_a },
    { key: 'B', label: currentQuestion.option_b },
    { key: 'C', label: currentQuestion.option_c },
    { key: 'D', label: currentQuestion.option_d },
  ]

  const getAnswerClasses = (option: 'A' | 'B' | 'C' | 'D') => {
    if (!showResults) {
      return selected === option
        ? 'bg-primary/10 border-primary'
        : 'bg-card border-border'
    }
    const isSelected = selected === option
    const isCorrect = currentQuestion.correct_option === option
    if (isCorrect) return 'bg-green-50 border-green-500 text-green-900'
    if (isSelected && !isCorrect) return 'bg-red-50 border-red-500 text-red-900'
    return 'bg-muted/50 border-border'
  }

  const getOptionText = (option: string) => {
    if (option === 'A') return currentQuestion.option_a
    if (option === 'B') return currentQuestion.option_b
    if (option === 'C') return currentQuestion.option_c
    return currentQuestion.option_d
  }

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="w-full max-w-3xl">
        <div className="bg-card border rounded-xl shadow-lg p-12">
          <div className="space-y-10">
            <div>
              <h3 className="text-lg font-medium leading-relaxed mb-6">
                {currentQuestion.question_text}
              </h3>
              {showResults && (
                <div className="flex items-center gap-2 mb-4">
                  {selected === currentQuestion.correct_option ? (
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
                  onClick={() => handleSelect(opt.key)}
                  disabled={showResults}
                  className={`text-left p-4 border rounded-lg transition-all ${
                    showResults
                      ? 'cursor-default'
                      : 'cursor-pointer hover:shadow-md'
                  } ${getAnswerClasses(opt.key)}`}
                >
                  <div className="flex gap-3">
                    <span className="font-semibold shrink-0">{opt.key}.</span>
                    <span className="leading-relaxed">{opt.label}</span>
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
                    {currentQuestion.correct_option}.{' '}
                    {getOptionText(currentQuestion.correct_option)}
                  </span>
                </div>
                {currentQuestion.explanation && (
                  <div className="text-sm text-muted-foreground leading-relaxed">
                    <span className="font-medium">Explanation: </span>
                    {currentQuestion.explanation}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
