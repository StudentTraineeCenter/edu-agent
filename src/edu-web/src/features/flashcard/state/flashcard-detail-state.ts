import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Layer, Option } from 'effect'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import type { PracticeRecordCreate } from '@/integrations/api'
import { ApiClientService } from '@/integrations/api'
import { submitPracticeRecordsBatchAtom } from '@/data-acess/practice'
import { flashcardsAtom } from '@/data-acess/flashcard'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

type FlashcardGroupKeyParams = {
  projectId: string
  flashcardGroupId: string
}

type FlashcardGroupKey =
  `${FlashcardGroupKeyParams['projectId']}:${FlashcardGroupKeyParams['flashcardGroupId']}`

type CardId = string

export type FlashcardDetailState = {
  readonly queue: ReadonlyArray<CardId> // Ordered queue of cards still in play
  readonly currentCardId: CardId | null
  readonly showAnswer: boolean
  readonly pendingPracticeRecords: Record<string, PracticeRecordCreate>
  readonly isCompleted: boolean
  readonly isReady: boolean // Whether the queue has been initialized at least once
  // Progress within this session
  readonly sessionCorrectIds: ReadonlySet<CardId>
  readonly sessionWrongIds: ReadonlySet<CardId>
  // Track initial unique cards in session (for progress calculation)
  readonly initialCardIds: ReadonlySet<CardId>
  // Optional: persisted mastery from server
  readonly masteredIds: ReadonlySet<CardId>
}

type FlashcardDetailAction = Data.TaggedEnum<{
  SetQueue: { readonly queue: ReadonlyArray<CardId> }
  SetCurrentCardId: { readonly cardId: CardId | null }
  SetShowAnswer: { readonly show: boolean }
  AddPracticeRecord: {
    readonly cardId: string
    readonly practiceRecord: PracticeRecordCreate
  }
  MarkCorrect: { readonly cardId: CardId }
  MarkWrong: { readonly cardId: CardId }
  SetCompleted: { readonly completed: boolean }
  ResetWrong: { readonly wrongCardIds: ReadonlySet<CardId> }
  Reset: {}
  ClearPracticeRecords: {}
  SetMasteredIds: { readonly masteredIds: ReadonlySet<CardId> }
}>
const FlashcardDetailAction = Data.taggedEnum<FlashcardDetailAction>()

const initialState: FlashcardDetailState = {
  queue: [],
  currentCardId: null,
  showAnswer: false,
  pendingPracticeRecords: {},
  isCompleted: false,
  isReady: false,
  sessionCorrectIds: new Set(),
  sessionWrongIds: new Set(),
  initialCardIds: new Set(),
  masteredIds: new Set(),
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
            SetQueue: ({ queue }) => {
              // Track initial unique cards when queue is set
              const initialCardIds = new Set([
                ...result.value.initialCardIds,
                ...queue,
              ])
              return {
                ...result.value,
                queue,
                currentCardId: queue.length > 0 ? queue[0] : null,
                showAnswer: false,
                initialCardIds,
                isReady: true,
              }
            },
            SetCurrentCardId: ({ cardId }) => {
              return { ...result.value, currentCardId: cardId }
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
            MarkCorrect: ({ cardId }) => {
              // Remove from queue, add to correct set, remove from wrong
              const newQueue = result.value.queue.filter((id) => id !== cardId)
              return {
                ...result.value,
                queue: newQueue,
                currentCardId: newQueue.length > 0 ? newQueue[0] : null,
                sessionCorrectIds: new Set([
                  ...result.value.sessionCorrectIds,
                  cardId,
                ]),
                sessionWrongIds: new Set(
                  Array.from(result.value.sessionWrongIds).filter(
                    (id) => id !== cardId,
                  ),
                ),
                isCompleted: newQueue.length === 0,
                showAnswer: false,
              }
            },
            MarkWrong: ({ cardId }) => {
              // Remove from queue, add to wrong set, remove from correct
              const newQueue = result.value.queue.filter((id) => id !== cardId)
              return {
                ...result.value,
                queue: newQueue,
                currentCardId: newQueue.length > 0 ? newQueue[0] : null,
                sessionWrongIds: new Set([
                  ...result.value.sessionWrongIds,
                  cardId,
                ]),
                sessionCorrectIds: new Set(
                  Array.from(result.value.sessionCorrectIds).filter(
                    (id) => id !== cardId,
                  ),
                ),
                isCompleted: newQueue.length === 0,
                showAnswer: false,
              }
            },
            SetCompleted: ({ completed }) => {
              return { ...result.value, isCompleted: completed }
            },
            ResetWrong: ({ wrongCardIds }) => {
              const wrongIdsArray = Array.from(wrongCardIds)
              const shuffled = shuffleArray(wrongIdsArray)
              return {
                ...initialState,
                queue: shuffled,
                initialCardIds: new Set(wrongIdsArray),
                currentCardId: shuffled.length > 0 ? shuffled[0] : null,
                isReady: true,
              }
            },
            Reset: () => {
              return { ...initialState }
            },
            ClearPracticeRecords: () => {
              return { ...result.value, pendingPracticeRecords: {} }
            },
            SetMasteredIds: ({ masteredIds }) => {
              return { ...result.value, masteredIds }
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

const currentFlashcardAtomFamily = Atom.family((key: FlashcardGroupKey) => {
  const [, flashcardGroupId] = key.split(':')
  return Atom.make(
    Effect.fn(function* (get) {
      const state = get(flashcardDetailStateAtom(flashcardGroupId))
      const flashcardsResult = get(flashcardsAtom(key))

      if (Option.isNone(state) || !Result.isSuccess(flashcardsResult)) {
        return null
      }

      const { currentCardId } = state.value
      if (!currentCardId) {
        console.log('No currentCardId in state', {
          flashcardGroupId,
          queueLength: state.value.queue.length,
        })
        return null
      }

      const flashcards = flashcardsResult.value
      const card = flashcards.find((f) => f.id === currentCardId)

      if (!card) {
        console.warn('Current card not found in flashcards', {
          currentCardId,
          flashcardGroupId,
          availableIds: flashcards.map((f) => f.id).slice(0, 5),
          totalFlashcards: flashcards.length,
        })
      }

      return card ?? null
    }),
  )
})

export const currentFlashcardAtom = ({
  projectId,
  flashcardGroupId,
}: FlashcardGroupKeyParams) => {
  const key = `${projectId}:${flashcardGroupId}`
  return currentFlashcardAtomFamily(key)
}

const answeredCardsAtomFamily = Atom.family((key: FlashcardGroupKey) => {
  const [, flashcardGroupId] = key.split(':')
  return Atom.make(
    Effect.fn(function* (get) {
      const state = get(flashcardDetailStateAtom(flashcardGroupId))
      const flashcardsResult = get(flashcardsAtom(key))

      if (Option.isNone(state) || !Result.isSuccess(flashcardsResult)) {
        return { correct: [], incorrect: [] }
      }

      const flashcards = flashcardsResult.value
      const { sessionCorrectIds, sessionWrongIds } = state.value

      const correct = flashcards.filter((f: { id: string }) =>
        sessionCorrectIds.has(f.id),
      )
      const incorrect = flashcards.filter((f: { id: string }) =>
        sessionWrongIds.has(f.id),
      )

      return { correct, incorrect }
    }),
  )
})

export const answeredCardsAtom = ({
  projectId,
  flashcardGroupId,
}: FlashcardGroupKeyParams) => {
  const key = `${projectId}:${flashcardGroupId}`
  return answeredCardsAtomFamily(key)
}

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
    practiceRecord: PracticeRecordCreate
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

export const resetWrongAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    wrongCardIds: ReadonlySet<string>
  }) {
    const registry = yield* Registry.AtomRegistry
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.ResetWrong({ wrongCardIds: input.wrongCardIds }),
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
        PracticeRecordCreate,
        ...Array<PracticeRecordCreate>,
      ],
    })

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.ClearPracticeRecords(),
    )
  }),
)

const extractTopic = (text: string, maxLength = 100): string => {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// Fisher-Yates shuffle
const shuffleArray = <T>(array: Array<T>): Array<T> => {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

export const initializeQueueAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardGroupId: string
    includeMastered?: boolean
  }) {
    const registry = yield* Registry.AtomRegistry

    // Get flashcards atom and wait for it to be ready
    const flashcardsAtomInstance = flashcardsAtom(
      `${input.projectId}:${input.flashcardGroupId}`,
    )

    // Wait for flashcards to load
    const flashcardsResult = yield* Effect.gen(function* () {
      // Try to get the result
      let result = registry.get(flashcardsAtomInstance)

      // If not success, wait a bit and try again (up to 10 times = 500ms max)
      let attempts = 0
      while (!Result.isSuccess(result) && attempts < 10) {
        yield* Effect.sleep(50)
        result = registry.get(flashcardsAtomInstance)
        attempts++
      }

      return result
    })

    if (!Result.isSuccess(flashcardsResult)) {
      console.warn(
        'Failed to load flashcards for queue initialization',
        flashcardsResult,
      )
      return
    }

    const flashcards = flashcardsResult.value

    if (!flashcards || flashcards.length === 0) {
      console.warn('No flashcards found for queue initialization', {
        flashcardGroupId: input.flashcardGroupId,
      })
      return
    }

    console.log('Initializing queue with flashcards', {
      count: flashcards.length,
      flashcardGroupId: input.flashcardGroupId,
    })

    const stateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    const state = Option.isSome(stateResult) ? stateResult.value : initialState

    // Filter to un-mastered by default (unless includeMastered is true)
    let cardsToInclude = flashcards
    if (!input.includeMastered) {
      cardsToInclude = flashcards.filter(
        (f: { id: string }) => !state.masteredIds.has(f.id),
      )
    }

    if (cardsToInclude.length === 0) {
      console.warn('No un-mastered flashcards to include in queue')
      return
    }

    // Shuffle the cards
    const cardIds = shuffleArray(
      cardsToInclude.map((card: { id: string }) => card.id),
    )

    console.log('Setting queue', {
      queueLength: cardIds.length,
      firstCardId: cardIds[0],
      flashcardGroupId: input.flashcardGroupId,
    })

    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.SetQueue({ queue: cardIds }),
    )
  }),
)

export const gotItRightAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry

    const currentStateResult = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isNone(currentStateResult)) return
    const currentState = currentStateResult.value

    const { currentCardId } = currentState
    if (!currentCardId) return

    const flashcardsResult = registry.get(
      flashcardsAtom(`${input.projectId}:${input.flashcardGroupId}`),
    )
    if (!Result.isSuccess(flashcardsResult)) return

    const flashcards = flashcardsResult.value
    const currentCard = flashcards.find(
      (f: { id: string }) => f.id === currentCardId,
    )
    if (!currentCard) return

    const practiceRecord: PracticeRecordCreate = {
      item_type: 'flashcard',
      item_id: currentCard.id,
      topic: extractTopic(currentCard.question),
      user_answer: undefined,
      correct_answer: currentCard.answer,
      was_correct: true,
    }

    // Add practice record
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddPracticeRecord({
        cardId: currentCard.id,
        practiceRecord,
      }),
    )

    // Mark as correct (removes from queue, updates sets)
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.MarkCorrect({ cardId: currentCard.id }),
    )

    // Check if queue is empty (session complete)
    const updatedState = registry.get(
      flashcardDetailStateAtom(input.flashcardGroupId),
    )
    if (Option.isSome(updatedState) && updatedState.value.queue.length === 0) {
      registry.set(
        flashcardDetailStateAtom(input.flashcardGroupId),
        FlashcardDetailAction.SetCompleted({ completed: true }),
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

    const { currentCardId } = currentState
    if (!currentCardId) return

    const flashcardsResult = registry.get(
      flashcardsAtom(`${input.projectId}:${input.flashcardGroupId}`),
    )
    if (!Result.isSuccess(flashcardsResult)) return

    const flashcards = flashcardsResult.value
    const currentCard = flashcards.find(
      (f: { id: string }) => f.id === currentCardId,
    )
    if (!currentCard) return

    const practiceRecord: PracticeRecordCreate = {
      item_type: 'flashcard',
      item_id: currentCard.id,
      topic: extractTopic(currentCard.question),
      user_answer: undefined,
      correct_answer: currentCard.answer,
      was_correct: false,
    }

    // Add practice record
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.AddPracticeRecord({
        cardId: currentCard.id,
        practiceRecord,
      }),
    )

    // Mark as incorrect (moves to end of queue, updates sets)
    registry.set(
      flashcardDetailStateAtom(input.flashcardGroupId),
      FlashcardDetailAction.MarkWrong({ cardId: currentCard.id }),
    )
  }),
)
