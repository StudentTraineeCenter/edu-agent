import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { HttpBody } from '@effect/platform'
import { runtime } from './runtime'
import { CreateNoteRequest } from '@/integrations/api/client'

export const notesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.listNotesV1NotesGet({
        project_id: projectId,
      })
    }),
  ).pipe(Atom.keepAlive),
)

export const noteAtom = Atom.family((noteId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.getNoteV1NotesNoteIdGet(noteId)
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
    input: { projectId: string; userPrompt?: string; length?: string },
    get: Atom.FnContext,
  ) {
    const httpClient = yield* makeHttpClient
    const body = HttpBody.unsafeJson(
      new CreateNoteRequest({
        user_prompt: input.userPrompt,
        length: input.length,
      }),
    )
    const resp = yield* httpClient.post(
      `/v1/notes/stream?project_id=${input.projectId}`,
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
  Effect.fn(function* (input: { projectId: string; userPrompt?: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createNoteV1NotesPost({
      params: { project_id: input.projectId },
      payload: new CreateNoteRequest({
        user_prompt: input.userPrompt,
      }),
    })

    registry.refresh(notesAtom(input.projectId))
    return resp.note
  }),
)

export const deleteNoteAtom = runtime.fn(
  Effect.fn(function* (input: { noteId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteNoteV1NotesNoteIdDelete(input.noteId)

    registry.refresh(notesAtom(input.projectId))
  }),
)
