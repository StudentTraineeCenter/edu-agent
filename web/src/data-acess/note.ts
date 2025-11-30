import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
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
