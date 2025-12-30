import { GenerateRequest, NoteCreate } from '@/integrations/api/client'
import { ApiClientService } from '@/integrations/api/http'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { withToast } from '@/lib/with-toast'
import { Atom, Registry } from '@effect-atom/atom-react'
import { HttpBody } from '@effect/platform'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Effect, Layer, Schema, Stream } from 'effect'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

export const notesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      return yield* apiClient.listNotesApiV1ProjectsProjectIdNotesGet(projectId)
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive),
)

export const noteAtom = Atom.family((input: string) => {
  const [projectId, noteId] = input.split(':')
  return Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      return yield* apiClient.getNoteApiV1ProjectsProjectIdNotesNoteIdGet(
        projectId,
        noteId,
      )
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive)
})

const NoteProgressUpdate = Schema.Struct({
  status: Schema.String,
  message: Schema.String,
  note_id: Schema.NullishOr(Schema.String),
  error: Schema.NullishOr(Schema.String),
})

export const noteProgressAtom = Atom.make<{
  status: string
  message: string
  error?: string
} | null>(null)

export const createNoteStreamAtom = Atom.fn(
  (
    input: {
      projectId: string
      noteId: string
      customInstructions?: string
      topic?: string
      count?: number
      difficulty?: string
    },
    _get,
  ) =>
    Effect.gen(function* () {
      const { httpClient } = yield* ApiClientService
      const body = HttpBody.unsafeJson(
        new GenerateRequest({
          custom_instructions: input.customInstructions,
          topic: input.topic,
          count: input.count,
          difficulty: input.difficulty,
        }),
      )
      const resp = yield* httpClient.post(
        `/api/v1/projects/${input.projectId}/notes/${input.noteId}/generate/stream`,
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
              Schema.decodeUnknown(Schema.parseJson(NoteProgressUpdate))(line),
            ),
          )
        }),
        Stream.tap((progress) =>
          Effect.gen(function* () {
            const registry = yield* Registry.AtomRegistry
            registry.set(noteProgressAtom, {
              status: progress.status,
              message: progress.message,
              error: progress.error ?? undefined,
            })
          }),
        ),
      )

      yield* Stream.runCollect(respStream)

      // Refresh notes list after completion
      const registry = yield* Registry.AtomRegistry
      if (input.projectId) {
        registry.refresh(notesAtom(input.projectId))
      }
      registry.set(noteProgressAtom, null)
    }).pipe(Effect.provide(ApiClientService.Default)),
).pipe(Atom.keepAlive)

export const createNoteAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    title?: string
    content?: string
    description?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp = yield* apiClient.createNoteApiV1ProjectsProjectIdNotesPost(
      input.projectId,
      new NoteCreate({
        title: input.title ?? 'New Note',
        content: input.content ?? '',
        description: input.description,
      }),
    )

    registry.refresh(notesAtom(input.projectId))
    return resp
  }),
)

export const deleteNoteAtom = runtime.fn(
  Effect.fn(
    function* (input: { noteId: string; projectId: string }) {
      const registry = yield* Registry.AtomRegistry
      const { apiClient } = yield* ApiClientService
      yield* apiClient.deleteNoteApiV1ProjectsProjectIdNotesNoteIdDelete(
        input.projectId,
        input.noteId,
      )

      registry.refresh(notesAtom(input.projectId))
    },
    withToast({
      onWaiting: () => 'Deleting note...',
      onSuccess: 'Note deleted',
      onFailure: 'Failed to delete note',
    }),
  ),
)
