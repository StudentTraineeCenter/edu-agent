import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Option } from 'effect'
import type { CreatePracticeRecordRequest } from '@/integrations/api'
import { runtime } from './runtime'
import { submitPracticeRecordsBatchAtom } from './practice'
import { flashcardsAtom } from './flashcard'

export type FlashcardDetailState = {
  readonly currentCardIndex: number
  readonly showAnswer: boolean
  readonly pendingPracticeRecords: Record<string, CreatePracticeRecordRequest>
  readonly markedCardIds: ReadonlySet<string>
  readonly isCompleted: boolean
}

type FlashcardDetailAction = Data.TaggedEnum<{
  SetCurrentCardIndex: { readonly index: number }
  SetShowAnswer: { readonly show: boolean }
  AddPracticeRecord: {
    readonly cardId: string
    readonly practiceRecord: CreatePracticeRecordRequest
  }
  MarkCard: { readonly cardId: string }
  SetCompleted: { readonly completed: boolean }
  Reset: {}
  ClearPracticeRecords: {}
}>
const FlashcardDetailAction = Data.taggedEnum<FlashcardDetailAction>()

// const attempts = Object.values(pendingAttempts)
//       const total = attempts.length
//       const correct = attempts.filter((a) => a.was_correct).length
//       const incorrect = attempts.filter((a) => !a.was_correct).length
//       const percentage = total > 0 ? Math.round((correct / total) * 100) : 0
//       return { total, correct, incorrect, percentage }

const initialState: FlashcardDetailState = {
  currentCardIndex: 0,
  showAnswer: false,
  pendingPracticeRecords: {},
  markedCardIds: new Set(),
  isCompleted: false,
}

export const flashcardDetailStateAtom = Atom.family(
  (flashcardGroupId: string) =>
    Object.assign(
      Atom.writable(
        (get: Atom.Context) => {
          const result = get.self<FlashcardDetailState>()
          if (Option.isNone(result)) return Option.some(initialState)
          return result
        },
        (ctx, action: FlashcardDetailAction) => {
          const result = ctx.get(flashcardDetailStateAtom(flashcardGroupId))
          if (Option.isNone(result)) return

          const update = FlashcardDetailAction.$match(action, {
            SetCurrentCardIndex: ({ index }) => {
              return { ...result.value, currentCardIndex: index }
            },
            SetShowAnswer: ({ show }) => {
              return { ...result.value, showAnswer: show }
            },
            AddPracticeRecord: (args) => {
              return {
                ...result.value,
                pendingPracticeRecords: {
                  ...result.value.pendingPracticeRecords,
                  [args.cardId]: args.practiceRecord,
                },
              }
            },
            MarkCard: ({ cardId }) => {
              return {
                ...result.value,
                markedCardIds: new Set([...result.value.markedCardIds, cardId]),
              }
            },
            SetCompleted: ({ completed }) => {
              return { ...result.value, isCompleted: completed }
            },
            Reset: () => {
              return initialState
            },
            ClearPracticeRecords: () => {
              return { ...result.value, pendingPracticeRecords: {} }
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

export const flashcardStatsAtom = Atom.family((flashcardGroupId: string) =>
  Atom.make(
    Effect.fn(function* (get) {
      const state = get(flashcardDetailStateAtom(flashcardGroupId))
      if (Option.isNone(state))
        return { total: 0, correct: 0, incorrect: 0, percentage: 0 }

      const pendingPracticeRecords = state.value.pendingPracticeRecords
      const practiceRecords = Object.values(pendingPracticeRecords)
      const total = practiceRecords.length
      const correct = practiceRecords.filter((a) => a.was_correct).length
      const incorrect = practiceRecords.filter((a) => !a.was_correct).length
      const percentage = total > 0 ? Math.round((correct / total) * 100) : 0
      return { total, correct, incorrect, percentage }
    }),
  ),
)

export const answeredCardsAtom = Atom.family((flashcardGroupId: string) =>
  Atom.make(
    Effect.fn(function* (get) {
      const state = get(flashcardDetailStateAtom(flashcardGroupId))
      if (Option.isNone(state)) return { correct: [], incorrect: [] }
      const pendingPracticeRecords = state.value.pendingPracticeRecords
      const practiceRecords = Object.values(pendingPracticeRecords)

      const flashcardsResult = get(flashcardsAtom(flashcardGroupId))
      if (!Result.isSuccess(flashcardsResult))
        return { correct: [], incorrect: [] }
      const flashcards = flashcardsResult.value.data

      const correct = flashcards.filter((f) =>
        practiceRecords.some((a) => a.item_id === f.id && a.was_correct),
      )
      const incorrect = flashcards.filter((f) =>
        practiceRecords.some((a) => a.item_id === f.id && !a.was_correct),
      )

      return { correct, incorrect }
    }),
  ),
)

export const setCurrentCardIndexAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; index: number }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetCurrentCardIndex({ index: input.index }),
    )
  }),
)

export const setShowAnswerAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; show: boolean }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetShowAnswer({ show: input.show }),
    )
  }),
)

export const addPracticeRecordAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    cardId: string
    practiceRecord: CreatePracticeRecordRequest
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddPracticeRecord({
        cardId: input.cardId,
        practiceRecord: input.practiceRecord,
      }),
    )
  }),
)

export const markCardAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; cardId: string }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.MarkCard({ cardId: input.cardId }),
    )
  }),
)

export const setCompletedAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    completed: boolean
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetCompleted({ completed: input.completed }),
    )
  }),
)

export const resetAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.Reset(),
    )
  }),
)

export const clearPracticeRecordsAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.ClearPracticeRecords(),
    )
  }),
)

export const submitPendingPracticeRecordsAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )

    if (Option.isNone(currentStateResult)) return

    const currentState = currentStateResult.value
    const pendingPracticeRecords = Object.values(
      currentState.pendingPracticeRecords ?? {},
    )
    if (pendingPracticeRecords.length === 0) return

    registry.set(submitPracticeRecordsBatchAtom, {
      projectId: input.projectId,
      practice_records: pendingPracticeRecords as unknown as [
        CreatePracticeRecordRequest,
        ...CreatePracticeRecordRequest[],
      ],
    })

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.ClearPracticeRecords(),
    )
  }),
)

export const goToNextCardAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const { currentCardIndex } = currentState

    const flashcardsResult = registry.get(
      flashcardsAtom(input.flashcardGroupId),
    )
    if (!Result.isSuccess(flashcardsResult)) return

    const flashcards = flashcardsResult.value.data
    const isLastCard = currentCardIndex === flashcards.length - 1

    if (isLastCard) {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCompleted({ completed: true }),
      )
      return
    }

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetCurrentCardIndex({
        index: currentCardIndex + 1,
      }),
    )
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetShowAnswer({ show: false }),
    )
  }),
)

export const goToPreviousCardAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const { currentCardIndex } = currentState

    const isFirstCard = currentCardIndex === 0
    if (isFirstCard) return

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetCurrentCardIndex({
        index: currentCardIndex - 1,
      }),
    )
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetShowAnswer({ show: false }),
    )
  }),
)

const extractTopic = (text: string, maxLength = 100): string => {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

export const gotItRightAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const flashcardsResult = registry.get(
      flashcardsAtom(input.flashcardGroupId),
    )
    if (!Result.isSuccess(flashcardsResult)) return

    const { currentCardIndex, markedCardIds } = currentState
    const flashcards = flashcardsResult.value.data

    const currentCard = flashcards[currentCardIndex]
    if (!currentCard) return

    if (markedCardIds.has(currentCard.id)) return

    const practiceRecord: CreatePracticeRecordRequest = {
      item_type: 'flashcard',
      item_id: currentCard.id,
      topic: extractTopic(currentCard.question),
      user_answer: undefined,
      correct_answer: currentCard.answer,
      was_correct: true,
    }

    const isLastCard = currentCardIndex === flashcards.length - 1

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddPracticeRecord({
        cardId: currentCard.id,
        practiceRecord,
      }),
    )

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.MarkCard({ cardId: currentCard.id }),
    )

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetShowAnswer({ show: false }),
    )

    if (isLastCard) {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCompleted({ completed: true }),
      )
    } else {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCurrentCardIndex({
          index: currentCardIndex + 1,
        }),
      )
    }
  }),
)

export const gotItWithQualityAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    projectId: string
    quality: number
  }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const flashcardsResult = registry.get(
      flashcardsAtom(input.flashcardGroupId),
    )
    if (!Result.isSuccess(flashcardsResult)) return

    const { currentCardIndex, markedCardIds } = currentState
    const flashcards = flashcardsResult.value.data

    const currentCard = flashcards[currentCardIndex]
    if (!currentCard) return

    if (markedCardIds.has(currentCard.id)) return

    // Quality 0-2 is wrong, 3-5 is right
    const wasCorrect = input.quality >= 3

    const practiceRecord: CreatePracticeRecordRequest = {
      item_type: 'flashcard',
      item_id: currentCard.id,
      topic: extractTopic(currentCard.question),
      user_answer: undefined,
      correct_answer: currentCard.answer,
      was_correct: wasCorrect,
      quality_rating: input.quality,
    }

    const isLastCard = currentCardIndex === flashcards.length - 1

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddPracticeRecord({
        cardId: currentCard.id,
        practiceRecord,
      }),
    )

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.MarkCard({ cardId: currentCard.id }),
    )

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetShowAnswer({ show: false }),
    )

    if (isLastCard) {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCompleted({ completed: true }),
      )
    } else {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCurrentCardIndex({
          index: currentCardIndex + 1,
        }),
      )
    }
  }),
)

export const gotItWrongAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const { currentCardIndex, markedCardIds } = currentState

    const flashcardsResult = registry.get(
      flashcardsAtom(input.flashcardGroupId),
    )
    if (!Result.isSuccess(flashcardsResult)) return
    const flashcards = flashcardsResult.value.data

    const currentCard = flashcards[currentCardIndex]
    if (!currentCard) return

    if (markedCardIds.has(currentCard.id)) return

    const practiceRecord: CreatePracticeRecordRequest = {
      item_type: 'flashcard',
      item_id: currentCard.id,
      topic: extractTopic(currentCard.question),
      user_answer: undefined,
      correct_answer: currentCard.answer,
      was_correct: false,
    }

    const isLastCard = currentCardIndex === flashcards.length - 1

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddPracticeRecord({
        cardId: currentCard.id,
        practiceRecord,
      }),
    )

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.MarkCard({ cardId: currentCard.id }),
    )

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetShowAnswer({ show: false }),
    )

    if (isLastCard) {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCompleted({ completed: true }),
      )
    } else {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCurrentCardIndex({
          index: currentCardIndex + 1,
        }),
      )
    }
  }),
)
