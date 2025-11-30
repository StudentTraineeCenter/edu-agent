import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { runtime } from './runtime'

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

export const deleteNoteAtom = runtime.fn(
  Effect.fn(function* (input: { noteId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteNoteV1NotesNoteIdDelete(input.noteId)

    registry.refresh(notesAtom(input.projectId))
  }),
)
