import { Atom, Registry } from '@effect-atom/atom-react'
import { ApiClientService } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { HttpBody } from '@effect/platform'
import {
  GenerateRequest,
  FlashcardCreate,
  FlashcardUpdate,
} from '@/integrations/api/client'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { withToast } from '@/lib/with-toast'
import { Layer } from 'effect'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

export const flashcardGroupsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      return yield* apiClient.listFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGet(
        projectId,
      )
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive),
)

export const flashcardGroupAtom = Atom.family(
  (input: { projectId: string; flashcardGroupId: string }) =>
    Atom.make(
      Effect.gen(function* () {
        const { apiClient } = yield* ApiClientService
        return yield* apiClient.getFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdGet(
          input.projectId,
          input.flashcardGroupId,
        )
      }).pipe(Effect.provide(ApiClientService.Default)),
    ).pipe(Atom.keepAlive),
)

export const flashcardsAtom = Atom.family(
  (input: { projectId: string; flashcardGroupId: string }) =>
    Atom.make(
      Effect.gen(function* () {
        const { apiClient } = yield* ApiClientService
        return yield* apiClient.listFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsGet(
          input.projectId,
          input.flashcardGroupId,
        )
      }).pipe(Effect.provide(ApiClientService.Default)),
    ).pipe(Atom.keepAlive),
)

const FlashcardProgressUpdate = Schema.Struct({
  status: Schema.String,
  message: Schema.String,
  group_id: Schema.NullishOr(Schema.String),
  error: Schema.NullishOr(Schema.String),
})

export const flashcardProgressAtom = Atom.make<{
  status: string
  message: string
  error?: string
} | null>(null)

export const createFlashcardGroupStreamAtom = runtime
  .fn(
    Effect.fn(function* (
      input: {
        projectId: string
        groupId: string
        flashcardCount?: number
        customInstructions?: string
        length?: string
        difficulty?: string
      },
      _get: Atom.FnContext,
    ) {
      const { httpClient } = yield* ApiClientService
      const body = HttpBody.unsafeJson(
        new GenerateRequest({
          count: input.flashcardCount,
          custom_instructions: input.customInstructions,
          difficulty: input.difficulty,
        }),
      )
      const resp = yield* httpClient.post(
        `/api/v1/projects/${input.projectId}/flashcard-groups/${input.groupId}/generate/stream`,
        { body },
      )

      const decoder = new TextDecoder()
      const respStream = resp.stream.pipe(
        Stream.map((value) => decoder.decode(value, { stream: true })),
        Stream.map((chunk) => {
          const chunkLines = chunk.split('\n')
          const res = chunkLines
            .map((line) =>
              line.startsWith('data: ') ? line.replace('data: ', '') : '',
            )
            .filter((line) => line !== '')
            .join('\n')
          return res
        }),
        Stream.filter((chunk) => chunk !== ''),
        Stream.flatMap((chunk) => {
          const lines = chunk.trim().split('\n')
          return Stream.fromIterable(lines).pipe(
            Stream.filter((line) => line.trim() !== ''),
            Stream.flatMap((line) =>
              Schema.decodeUnknown(Schema.parseJson(FlashcardProgressUpdate))(
                line,
              ),
            ),
          )
        }),
        Stream.tap((progress) =>
          Effect.gen(function* () {
            const registry = yield* Registry.AtomRegistry
            registry.set(flashcardProgressAtom, {
              status: progress.status,
              message: progress.message,
              error: progress.error ?? undefined,
            })
          }),
        ),
      )

      yield* Stream.runCollect(respStream)

      // Refresh flashcard groups list after completion
      const registry = yield* Registry.AtomRegistry
      if (input.projectId) {
        registry.refresh(flashcardGroupsAtom(input.projectId))
      }
      registry.set(flashcardProgressAtom, null)
    }),
  )
  .pipe(Atom.keepAlive)

export const createFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardCount?: number
    customInstructions?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.createFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsPost(
        input.projectId,
        {
          name: 'New Flashcard Group',
          description: 'Description of the flashcard group',
        },
      )

    registry.refresh(flashcardGroupsAtom(input.projectId))
    return resp
  }),
)

export const deleteFlashcardGroupAtom = runtime.fn(
  Effect.fn(
    function* (input: { flashcardGroupId: string; projectId: string }) {
      const registry = yield* Registry.AtomRegistry
      const { apiClient } = yield* ApiClientService
      yield* apiClient.deleteFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdDelete(
        input.projectId,
        input.flashcardGroupId,
      )

      registry.refresh(flashcardGroupsAtom(input.projectId))
    },
    withToast({
      onWaiting: () => 'Deleting flashcard group...',
      onSuccess: 'Flashcard group deleted',
      onFailure: 'Failed to delete flashcard group',
    }),
  ),
)

export const exportFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (_input: { flashcardGroupId: string }) {
    // Note: Flashcard group export endpoints may not be available in the new API
    // const client = yield* makeApiClient
    // const response = yield* client.exportFlashcardGroup(...)
    throw new Error('Flashcard group export not supported in current API')
  }),
)

export const importFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; file: File }) {
    const registry = yield* Registry.AtomRegistry
    // Note: Flashcard group import endpoints may not be available in the new API
    // const client = yield* makeApiClient
    // const response = yield* client.importFlashcardGroup(...)

    registry.refresh(flashcardGroupsAtom(input.projectId))
    throw new Error('Flashcard group import not supported in current API')
  }),
)

export const createFlashcardAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardGroupId: string
    question: string
    answer: string
    difficultyLevel?: string
    position?: number
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.createFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsPost(
        input.projectId,
        input.flashcardGroupId,
        new FlashcardCreate({
          question: input.question,
          answer: input.answer,
          difficulty_level: input.difficultyLevel || 'medium',
          position: input.position,
        }),
      )

    registry.refresh(
      flashcardsAtom({
        projectId: input.projectId,
        flashcardGroupId: input.flashcardGroupId,
      }),
    )
    return resp
  }),
)

export const updateFlashcardAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardId: string
    flashcardGroupId: string
    question?: string
    answer?: string
    difficultyLevel?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.updateFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdPatch(
        input.projectId,
        input.flashcardGroupId,
        input.flashcardId,
        new FlashcardUpdate({
          question: input.question,
          answer: input.answer,
          difficulty_level: input.difficultyLevel,
        }),
      )

    registry.refresh(
      flashcardsAtom({
        projectId: input.projectId,
        flashcardGroupId: input.flashcardGroupId,
      }),
    )
    return resp
  }),
)

export const reorderFlashcardsAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardGroupId: string
    flashcardIds: string[]
  }) {
    const registry = yield* Registry.AtomRegistry
    // Note: Flashcard reorder endpoints may not be available in the new API
    // This might need to be handled differently or removed if not supported
    // For now, commenting out as the endpoint doesn't exist in the client
    // const client = yield* makeApiClient
    // const resp = yield* client.reorderFlashcards(...)

    registry.refresh(
      flashcardsAtom({
        projectId: input.projectId,
        flashcardGroupId: input.flashcardGroupId,
      }),
    )
    // return resp.data
    throw new Error('Flashcard reordering not supported in current API')
  }),
)

export const deleteFlashcardAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardId: string
    flashcardGroupId: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    yield* apiClient.deleteFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdDelete(
      input.projectId,
      input.flashcardGroupId,
      input.flashcardId,
    )

    registry.refresh(
      flashcardsAtom({
        projectId: input.projectId,
        flashcardGroupId: input.flashcardGroupId,
      }),
    )
  }),
)
