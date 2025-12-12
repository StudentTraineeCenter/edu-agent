import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { HttpBody } from '@effect/platform'
import { runtime } from './runtime'
import { NoteCreate, GenerateRequest } from '@/integrations/api/client'

export const notesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.listNotesApiV1ProjectsProjectIdNotesGet(projectId)
    }),
  ).pipe(Atom.keepAlive),
)

export const noteAtom = Atom.family(
  (input: { projectId: string; noteId: string }) =>
    Atom.make(
      Effect.gen(function* () {
        const client = yield* makeApiClient
        return yield* client.getNoteApiV1ProjectsProjectIdNotesNoteIdGet(
          input.projectId,
          input.noteId,
        )
      }),
    ).pipe(Atom.keepAlive),
)

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
  Effect.fn(function* (
    input: {
      projectId: string
      noteId: string
      customInstructions?: string
      topic?: string
      count?: number
      difficulty?: string
    },
    _get: Atom.FnContext,
  ) {
    const httpClient = yield* makeHttpClient
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
  }),
).pipe(Atom.keepAlive)

export const createNoteAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    title?: string
    content?: string
    description?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createNoteApiV1ProjectsProjectIdNotesPost(
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
  Effect.fn(function* (input: { noteId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteNoteApiV1ProjectsProjectIdNotesNoteIdDelete(
      input.projectId,
      input.noteId,
    )

    registry.refresh(notesAtom(input.projectId))
  }),
)
