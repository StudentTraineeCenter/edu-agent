import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Option } from 'effect'
import type { CreateAttemptRequest } from '@/integrations/api'
import { runtime } from './runtime'
import { submitAttemptsBatchAtom } from './attempt'
import { flashcardsAtom } from './flashcard'

export type FlashcardDetailState = {
  readonly currentCardIndex: number
  readonly showAnswer: boolean
  readonly pendingAttempts: Record<string, CreateAttemptRequest>
  readonly markedCardIds: ReadonlySet<string>
  readonly isCompleted: boolean
}

type FlashcardDetailAction = Data.TaggedEnum<{
  SetCurrentCardIndex: { readonly index: number }
  SetShowAnswer: { readonly show: boolean }
  AddAttempt: {
    readonly cardId: string
    readonly attempt: CreateAttemptRequest
  }
  MarkCard: { readonly cardId: string }
  SetCompleted: { readonly completed: boolean }
  Reset: {}
  ClearAttempts: {}
}>
const FlashcardDetailAction = Data.taggedEnum<FlashcardDetailAction>()

const initialState: FlashcardDetailState = {
  currentCardIndex: 0,
  showAnswer: false,
  pendingAttempts: {},
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
            AddAttempt: (args) => {
              return {
                ...result.value,
                pendingAttempts: {
                  ...result.value.pendingAttempts,
                  [args.cardId]: args.attempt,
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
            ClearAttempts: () => {
              return { ...result.value, pendingAttempts: {} }
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

export const addAttemptAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    cardId: string
    attempt: CreateAttemptRequest
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddAttempt({
        cardId: input.cardId,
        attempt: input.attempt,
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

export const clearAttemptsAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.ClearAttempts(),
    )
  }),
)

export const submitPendingAttemptsAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )

    if (Option.isNone(currentStateResult)) return

    const currentState = currentStateResult.value
    const pendingAttempts = Object.values(currentState.pendingAttempts ?? {})
    if (pendingAttempts.length === 0) return

    registry.set(submitAttemptsBatchAtom, {
      projectId: input.projectId,
      attempts: pendingAttempts as unknown as [
        CreateAttemptRequest,
        ...CreateAttemptRequest[],
      ],
    })

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.ClearAttempts(),
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

    const { flashcards } = flashcardsResult.value
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
    const { flashcards } = flashcardsResult.value

    const currentCard = flashcards[currentCardIndex]
    if (!currentCard) return

    if (markedCardIds.has(currentCard.id)) return

    const attempt: CreateAttemptRequest = {
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
      FlashcardDetailAction.AddAttempt({
        cardId: currentCard.id,
        attempt,
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
    const { flashcards } = flashcardsResult.value

    const currentCard = flashcards[currentCardIndex]
    if (!currentCard) return

    if (markedCardIds.has(currentCard.id)) return

    const attempt: CreateAttemptRequest = {
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
      FlashcardDetailAction.AddAttempt({
        cardId: currentCard.id,
        attempt,
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
