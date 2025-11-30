import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
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
