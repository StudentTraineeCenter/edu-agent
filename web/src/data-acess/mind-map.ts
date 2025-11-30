import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { runtime } from './runtime'

export const mindMapsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const apiClient = yield* makeApiClient
      const mindMaps =
        yield* apiClient.listMindMapsV1ProjectsProjectIdMindMapsGet(projectId)
      return mindMaps
    }),
  ).pipe(Atom.keepAlive),
)

export const mindMapAtom = Atom.family((mindMapId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const apiClient = yield* makeApiClient
      const mindMap = yield* apiClient
        .getMindMapV1MindMapsMindMapIdGet(mindMapId)
        .pipe(
          Effect.catchTag('ResponseError', (error) => {
            if (error.response.status === 404) {
              return Effect.succeed(null)
            }
            return Effect.fail(error)
          }),
        )

      return mindMap
    }),
  ).pipe(Atom.keepAlive),
)

export const generateMindMapAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; userPrompt?: string }) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const mindMap =
      yield* apiClient.generateMindMapV1ProjectsProjectIdMindMapsPost(
        input.projectId,
        {
          user_prompt: input.userPrompt || null,
        },
      )
    // Refresh both the list and the individual mind map atom
    registry.refresh(mindMapsAtom(input.projectId))
    registry.refresh(mindMapAtom(mindMap.id))
    return mindMap
  }),
)
