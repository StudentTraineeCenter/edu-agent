import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Option } from 'effect'
import type {
  CreatePracticeRecordRequest,
  FlashcardDto,
} from '@/integrations/api'
import { runtime } from './runtime'
import { submitPracticeRecordsBatchAtom } from './practice'
import { flashcardsAtom } from './flashcard'

export type FlashcardMode = 'normal' | 'cycle-until-correct'

export type FlashcardDetailState = {
  readonly currentCardIndex: number
  readonly showAnswer: boolean
  readonly pendingPracticeRecords: Record<string, CreatePracticeRecordRequest>
  readonly markedCardIds: ReadonlySet<string>
  readonly isCompleted: boolean
  readonly mode: FlashcardMode
  readonly currentRound: number
  readonly wrongCardIds: ReadonlySet<string>
  readonly filteredCardIds: ReadonlySet<string> // Cards to show in current round
  readonly shuffledOrder: readonly string[] // Shuffled order of card IDs
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
  SetMode: { readonly mode: FlashcardMode }
  StartNewRound: { readonly wrongCardIds: ReadonlySet<string> }
  AddWrongCard: { readonly cardId: string }
  Shuffle: { readonly cardIds: readonly string[] }
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
  mode: 'normal',
  currentRound: 1,
  wrongCardIds: new Set(),
  filteredCardIds: new Set(),
  shuffledOrder: [],
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
            AddWrongCard: ({ cardId }) => {
              return {
                ...result.value,
                wrongCardIds: new Set([...result.value.wrongCardIds, cardId]),
              }
            },
            SetCompleted: ({ completed }) => {
              return { ...result.value, isCompleted: completed }
            },
            Reset: () => {
              // Preserve mode when resetting
              const currentMode = result.value.mode
              return {
                ...initialState,
                mode: currentMode,
              }
            },
            ClearPracticeRecords: () => {
              return { ...result.value, pendingPracticeRecords: {} }
            },
            SetMode: ({ mode }) => {
              return { ...result.value, mode }
            },
            StartNewRound: ({ wrongCardIds }) => {
              // Start new round with wrong cards from previous round
              // Reset marked cards and tracking, but keep the wrong cards as filtered
              return {
                ...result.value,
                currentRound: result.value.currentRound + 1,
                wrongCardIds: new Set() as ReadonlySet<string>, // Reset to track new wrong cards
                filteredCardIds: new Set(wrongCardIds) as ReadonlySet<string>, // Filter to wrong cards
                currentCardIndex: 0,
                markedCardIds: new Set() as ReadonlySet<string>,
                showAnswer: false,
                isCompleted: false,
              }
            },
            Shuffle: ({ cardIds }) => {
              // Shuffle the cards and reset to first card
              return {
                ...result.value,
                shuffledOrder: cardIds,
                currentCardIndex: 0,
                showAnswer: false,
              }
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

export const filteredFlashcardsAtom = Atom.family((flashcardGroupId: string) =>
  Atom.make(
    Effect.fn(function* (get) {
      const state = get(flashcardDetailStateAtom(flashcardGroupId))
      const flashcardsResult = get(flashcardsAtom(flashcardGroupId))

      if (!Result.isSuccess(flashcardsResult) || Option.isNone(state)) {
        return []
      }

      const flashcards = flashcardsResult.value.data
      const { mode, filteredCardIds, currentRound, shuffledOrder } = state.value

      // In cycle mode, filter to wrong cards after round 1
      let filteredCards =
        mode === 'cycle-until-correct' && currentRound > 1
          ? flashcards.filter((f) => filteredCardIds.has(f.id))
          : flashcards

      // Apply shuffle order if available
      if (shuffledOrder.length > 0) {
        const cardMap = new Map(filteredCards.map((card) => [card.id, card]))
        const shuffledCards = shuffledOrder
          .map((id) => cardMap.get(id))
          .filter(
            (card): card is NonNullable<typeof card> => card !== undefined,
          )
        // Add any cards not in shuffled order (shouldn't happen, but safety check)
        const shuffledIds = new Set(shuffledOrder)
        const missingCards = filteredCards.filter(
          (card) => !shuffledIds.has(card.id),
        )
        return [...shuffledCards, ...missingCards]
      }

      return filteredCards
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

export const setModeAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    mode: FlashcardMode
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetMode({ mode: input.mode }),
    )
  }),
)

export const startNewRoundAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    wrongCardIds: ReadonlySet<string>
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.StartNewRound({ wrongCardIds: input.wrongCardIds }),
    )
  }),
)

export const shuffleFlashcardsAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const registry = yield* Registry.AtomRegistry

    const flashcardsResult = registry.get(
      flashcardsAtom(input.flashcardGroupId),
    )
    if (!Result.isSuccess(flashcardsResult)) return

    const stateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(stateResult)) return

    const state = stateResult.value
    const { mode, filteredCardIds, currentRound } = state

    // Get the cards that should be shuffled (based on current filter)
    const allFlashcards = flashcardsResult.value.data
    const cardsToShuffle =
      mode === 'cycle-until-correct' && currentRound > 1
        ? allFlashcards.filter((f) => filteredCardIds.has(f.id))
        : allFlashcards

    // Create shuffled array of card IDs
    const cardIds = [...cardsToShuffle.map((card) => card.id)]
    // Fisher-Yates shuffle
    for (let i = cardIds.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[cardIds[i], cardIds[j]] = [cardIds[j], cardIds[i]]
    }

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.Shuffle({ cardIds }),
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

    const allFlashcards = flashcardsResult.value.data

    // Get filtered flashcards with shuffle applied
    const flashcards = getFilteredFlashcards(allFlashcards, currentState)

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

// Helper function to get filtered flashcards with shuffle applied
const getFilteredFlashcards = (
  allFlashcards: ReadonlyArray<FlashcardDto>,
  state: FlashcardDetailState,
): ReadonlyArray<FlashcardDto> => {
  const { mode, filteredCardIds, currentRound, shuffledOrder } = state

  // In cycle mode, filter to wrong cards after round 1
  let filteredCards =
    mode === 'cycle-until-correct' && currentRound > 1
      ? allFlashcards.filter((f) => filteredCardIds.has(f.id))
      : allFlashcards

  // Apply shuffle order if available
  if (shuffledOrder.length > 0) {
    const cardMap = new Map(filteredCards.map((card) => [card.id, card]))
    const shuffledCards = shuffledOrder
      .map((id) => cardMap.get(id))
      .filter((card): card is FlashcardDto => card !== undefined)
    // Add any cards not in shuffled order (shouldn't happen, but safety check)
    const shuffledIds = new Set(shuffledOrder)
    const missingCards = filteredCards.filter(
      (card) => !shuffledIds.has(card.id),
    )
    return [...shuffledCards, ...missingCards] as ReadonlyArray<FlashcardDto>
  }

  return filteredCards
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
    const allFlashcards = flashcardsResult.value.data

    // Get filtered flashcards with shuffle applied
    const flashcards = getFilteredFlashcards(allFlashcards, currentState)

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
    const allFlashcards = flashcardsResult.value.data

    // Get filtered flashcards with shuffle applied
    const flashcards = getFilteredFlashcards(allFlashcards, currentState)

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

    // Track wrong card for cycle mode
    if (!wasCorrect) {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.AddWrongCard({ cardId: currentCard.id }),
      )
    }

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

    const {
      currentCardIndex,
      markedCardIds,
      mode,
      filteredCardIds,
      currentRound,
    } = currentState

    const flashcardsResult = registry.get(
      flashcardsAtom(input.flashcardGroupId),
    )
    if (!Result.isSuccess(flashcardsResult)) return
    const allFlashcards = flashcardsResult.value.data

    // Get filtered flashcards based on mode
    const flashcards =
      mode === 'cycle-until-correct' && currentRound > 1
        ? allFlashcards.filter((f) => filteredCardIds.has(f.id))
        : allFlashcards

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

    // Track wrong card for cycle mode
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddWrongCard({ cardId: currentCard.id }),
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
