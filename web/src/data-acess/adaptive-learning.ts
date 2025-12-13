import { Atom } from '@effect-atom/atom-react'
import { ApiClientService } from '@/integrations/api/http'
import { Effect, Layer } from 'effect'
import { StudySessionCreate } from '@/integrations/api/client'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
export { StudySessionDto } from '@/integrations/api/client'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

export const generateStudySessionAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    sessionLengthMinutes?: number
    focusTopics?: string[]
  }) {
    const { apiClient } = yield* ApiClientService
    const response =
      yield* apiClient.createStudySessionApiV1ProjectsProjectIdStudySessionsPost(
        input.projectId,
        new StudySessionCreate({
          session_length_minutes: input.sessionLengthMinutes,
          focus_topics: input.focusTopics,
        }),
      )
    return response
  }),
)

export const getStudySessionAtom = Atom.family((sessionId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      return yield* apiClient.getStudySessionApiV1StudySessionsSessionIdGet(
        sessionId,
      )
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive),
)

export const listStudySessionsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      if (!projectId) return []
      const response =
        yield* apiClient.listStudySessionsApiV1ProjectsProjectIdStudySessionsGet(
          projectId,
        )
      return response
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive),
)
