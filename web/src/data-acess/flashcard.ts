import { Atom } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'

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
