import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { HttpBody } from '@effect/platform'
import { runtime } from './runtime'
import { CreateFlashcardGroupRequest } from '@/integrations/api/client'

export const flashcardGroupsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.listFlashcardGroupsV1FlashcardsGet({
        project_id: projectId,
      })
    }),
  ).pipe(Atom.keepAlive),
)

export const flashcardGroupAtom = Atom.family((flashcardGroupId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.getFlashcardGroupV1FlashcardsGroupIdGet(
        flashcardGroupId,
      )
    }),
  ).pipe(Atom.keepAlive),
)

export const flashcardsAtom = Atom.family((flashcardGroupId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.listFlashcardsV1FlashcardsGroupIdFlashcardsGet(
        flashcardGroupId,
      )
    }),
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

export const createFlashcardGroupStreamAtom = Atom.fn(
  Effect.fn(function* (
    input: {
      projectId: string
      flashcardCount?: number
      userPrompt?: string
      length?: string
      difficulty?: string
    },
    _get: Atom.FnContext,
  ) {
    const httpClient = yield* makeHttpClient
    const body = HttpBody.unsafeJson(
      new CreateFlashcardGroupRequest({
        flashcard_count: input.flashcardCount,
        user_prompt: input.userPrompt,
        length: input.length,
        difficulty: input.difficulty,
      }),
    )
    const resp = yield* httpClient.post(
      `/v1/flashcards/stream?project_id=${input.projectId}`,
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
).pipe(Atom.keepAlive)

export const createFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    flashcardCount?: number
    userPrompt?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createFlashcardGroupV1FlashcardsPost({
      params: { project_id: input.projectId },
      payload: new CreateFlashcardGroupRequest({
        flashcard_count: input.flashcardCount,
        user_prompt: input.userPrompt,
      }),
    })

    registry.refresh(flashcardGroupsAtom(input.projectId))
    return resp.flashcard_group
  }),
)

export const deleteFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteFlashcardGroupV1FlashcardsGroupIdDelete(
      input.flashcardGroupId,
    )

    registry.refresh(flashcardGroupsAtom(input.projectId))
  }),
)

export const exportFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (input: { flashcardGroupId: string }) {
    const client = yield* makeApiClient
    const response =
      yield* client.exportFlashcardGroupV1FlashcardsGroupIdExportGet(
        input.flashcardGroupId,
      )
    return response
  }),
)

export const importFlashcardGroupAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; file: File }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient

    const formData = new FormData()
    formData.append('file', input.file)

    const response =
      yield* client.importFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost(
        input.projectId,
        {
          file: input.file,
          group_name: '',
          group_description: '',
        },
      )

    registry.refresh(flashcardGroupsAtom(input.projectId))
    return response
  }),
)

export const createFlashcardAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    question: string
    answer: string
    difficultyLevel?: string
    position?: number
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createFlashcardV1FlashcardsGroupIdFlashcardsPost(
      input.flashcardGroupId,
      {
        question: input.question,
        answer: input.answer,
        difficulty_level: input.difficultyLevel || 'medium',
        position: input.position,
      },
    )

    registry.refresh(flashcardsAtom(input.flashcardGroupId))
    return resp.flashcard
  }),
)

export const updateFlashcardAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardId: string
    flashcardGroupId: string
    question?: string
    answer?: string
    difficultyLevel?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp =
      yield* client.updateFlashcardV1FlashcardsFlashcardsFlashcardIdPut(
        input.flashcardId,
        {
          question: input.question,
          answer: input.answer,
          difficulty_level: input.difficultyLevel,
        },
      )

    registry.refresh(flashcardsAtom(input.flashcardGroupId))
    return resp.flashcard
  }),
)

export const reorderFlashcardsAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardGroupId: string
    flashcardIds: string[]
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.reorderFlashcardsV1FlashcardsGroupIdReorderPatch(
      input.flashcardGroupId,
      {
        flashcard_ids: input.flashcardIds,
      },
    )

    registry.refresh(flashcardsAtom(input.flashcardGroupId))
    return resp.data
  }),
)

export const deleteFlashcardAtom = runtime.fn(
  Effect.fn(function* (input: {
    flashcardId: string
    flashcardGroupId: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteFlashcardV1FlashcardsFlashcardsFlashcardIdDelete(
      input.flashcardId,
    )

    registry.refresh(flashcardsAtom(input.flashcardGroupId))
  }),
)
