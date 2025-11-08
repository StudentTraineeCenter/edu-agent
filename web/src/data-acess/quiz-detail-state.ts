import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Option } from 'effect'
import type { CreateAttemptRequest } from '@/integrations/api'
import { runtime } from './runtime'
import { submitAttemptsBatchAtom } from './attempt'
import { quizQuestionsAtom } from './quiz'

export type QuizDetailState = {
  readonly currentQuestionIndex: number
  readonly showResults: boolean
  readonly pendingMistakes: Record<string, CreateAttemptRequest>
  readonly selectedByQuestionId: Record<string, 'A' | 'B' | 'C' | 'D'>
}

type QuizDetailAction = Data.TaggedEnum<{
  SetCurrentQuestionIndex: { readonly index: number }
  SetShowResults: { readonly show: boolean }
  SetSelectedAnswer: {
    readonly questionId: string
    readonly option: 'A' | 'B' | 'C' | 'D'
  }
  SetPendingMistakes: {
    readonly mistakes: Record<string, CreateAttemptRequest>
  }
  Reset: {}
  ClearMistakes: {}
}>

const QuizDetailAction = Data.taggedEnum<QuizDetailAction>()

const initialState: QuizDetailState = {
  currentQuestionIndex: 0,
  showResults: false,
  pendingMistakes: {},
  selectedByQuestionId: {},
}

export const quizDetailStateAtom = Atom.family((quizId: string) =>
  Object.assign(
    Atom.writable(
      (get: Atom.Context) => {
        const result = get.self<QuizDetailState>()
        if (Option.isNone(result)) return Option.some(initialState)
        return result
      },
      (ctx, action: QuizDetailAction) => {
        const result = ctx.get(quizDetailStateAtom(quizId))
        if (Option.isNone(result)) return

        const update = QuizDetailAction.$match(action, {
          SetCurrentQuestionIndex: ({ index }) => {
            return { ...result.value, currentQuestionIndex: index }
          },
          SetShowResults: ({ show }) => {
            return { ...result.value, showResults: show }
          },
          SetSelectedAnswer: ({ questionId, option }) => {
            return {
              ...result.value,
              selectedByQuestionId: {
                ...result.value.selectedByQuestionId,
                [questionId]: option,
              },
            }
          },
          SetPendingMistakes: ({ mistakes }) => {
            return { ...result.value, pendingMistakes: mistakes }
          },
          Reset: () => {
            return initialState
          },
          ClearMistakes: () => {
            return { ...result.value, pendingMistakes: {} }
          },
        })

        ctx.setSelf(Option.some(update))
      },
    ),
    {
      initial: initialState,
    },
  ),
)

export const quizStatsAtom = Atom.family((quizId: string) =>
  Atom.make(
    Effect.fn(function* (get) {
      const state = get(quizDetailStateAtom(quizId))
      if (Option.isNone(state))
        return { total: 0, correct: 0, incorrect: 0, percentage: 0 }

      if (!state.value.showResults)
        return { total: 0, correct: 0, incorrect: 0, percentage: 0 }

      const questionsResult = get(quizQuestionsAtom(quizId))
      if (!Result.isSuccess(questionsResult))
        return { total: 0, correct: 0, incorrect: 0, percentage: 0 }

      const quizQuestions = questionsResult.value
      const { selectedByQuestionId } = state.value

      const total = quizQuestions.length
      const correct = quizQuestions.reduce((acc, q) => {
        return (
          acc +
          (selectedByQuestionId[q.id] === (q.correct_option as any) ? 1 : 0)
        )
      }, 0)
      const incorrect = total - correct
      const percentage = total > 0 ? Math.round((correct / total) * 100) : 0

      return { total, correct, incorrect, percentage }
    }),
  ),
)

export const currentQuestionAtom = Atom.family((quizId: string) =>
  Atom.make(
    Effect.fn(function* (get) {
      const state = get(quizDetailStateAtom(quizId))
      if (Option.isNone(state)) return null

      const questionsResult = get(quizQuestionsAtom(quizId))
      if (!Result.isSuccess(questionsResult)) return null

      const quizQuestions = questionsResult.value
      const { currentQuestionIndex } = state.value

      return quizQuestions[currentQuestionIndex] ?? null
    }),
  ),
)

export const canSubmitQuizAtom = Atom.family((quizId: string) =>
  Atom.make(
    Effect.fn(function* (get) {
      const state = get(quizDetailStateAtom(quizId))
      if (Option.isNone(state)) return false

      const questionsResult = get(quizQuestionsAtom(quizId))
      if (!Result.isSuccess(questionsResult)) return false

      const quizQuestions = questionsResult.value
      const { selectedByQuestionId } = state.value

      return Object.keys(selectedByQuestionId).length === quizQuestions.length
    }),
  ),
)

export const setCurrentQuestionIndexAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; index: number }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetCurrentQuestionIndex({ index: input.index }),
    )
  }),
)

export const setShowResultsAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; show: boolean }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetShowResults({ show: input.show }),
    )
  }),
)

export const setSelectedAnswerAtom = runtime.fn(
  Effect.fn(function* (input: {
    quizId: string
    questionId: string
    option: 'A' | 'B' | 'C' | 'D'
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetSelectedAnswer({
        questionId: input.questionId,
        option: input.option,
      }),
    )
  }),
)

export const setPendingMistakesAtom = runtime.fn(
  Effect.fn(function* (input: {
    quizId: string
    mistakes: Record<string, CreateAttemptRequest>
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetPendingMistakes({ mistakes: input.mistakes }),
    )
  }),
)

export const resetQuizAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(quizDetailStateAtom(input.quizId), QuizDetailAction.Reset())
  }),
)

export const clearMistakesAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.ClearMistakes(),
    )
  }),
)

const extractTopic = (text: string, maxLength = 100): string => {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

export const submitQuizAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(quizDetailStateAtom(input.quizId))
    if (Option.isNone(currentStateResult)) return

    const currentState = currentStateResult.value
    const { selectedByQuestionId } = currentState

    const questionsResult = registry.get(quizQuestionsAtom(input.quizId))
    if (!Result.isSuccess(questionsResult)) return

    const quizQuestions = questionsResult.value

    // Track mistakes (only incorrect answers)
    const mistakes: Record<string, CreateAttemptRequest> = {}

    for (const q of quizQuestions) {
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
    }

    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetShowResults({ show: true }),
    )
    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetPendingMistakes({ mistakes }),
    )
  }),
)

export const submitPendingMistakesAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(quizDetailStateAtom(input.quizId))
    if (Option.isNone(currentStateResult)) return

    const currentState = currentStateResult.value
    const pendingMistakes = Object.values(currentState.pendingMistakes ?? {})
    if (pendingMistakes.length === 0) return

    registry.set(submitAttemptsBatchAtom, {
      projectId: input.projectId,
      attempts: pendingMistakes as unknown as [
        CreateAttemptRequest,
        ...CreateAttemptRequest[],
      ],
    })

    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.ClearMistakes(),
    )
  }),
)

export const goToNextQuestionAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(quizDetailStateAtom(input.quizId))
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const { currentQuestionIndex } = currentState

    const questionsResult = registry.get(quizQuestionsAtom(input.quizId))
    if (!Result.isSuccess(questionsResult)) return

    const quizQuestions = questionsResult.value
    const isLastQuestion = currentQuestionIndex === quizQuestions.length - 1

    if (isLastQuestion) return

    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetCurrentQuestionIndex({
        index: currentQuestionIndex + 1,
      }),
    )
  }),
)

export const goToPreviousQuestionAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(quizDetailStateAtom(input.quizId))
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const { currentQuestionIndex } = currentState

    const isFirstQuestion = currentQuestionIndex === 0
    if (isFirstQuestion) return

    registry.set(
      quizDetailStateAtom(input.quizId),
      QuizDetailAction.SetCurrentQuestionIndex({
        index: currentQuestionIndex - 1,
      }),
    )
  }),
)
