import { Atom } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { runtime } from './runtime'
import { StudySessionCreate } from '@/integrations/api/client'

export { StudySessionDto } from '@/integrations/api/client'

export const generateStudySessionAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    sessionLengthMinutes?: number
    focusTopics?: string[]
  }) {
    const client = yield* makeApiClient
    const response =
      yield* client.createStudySessionApiV1ProjectsProjectIdStudySessionsPost(
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
      const client = yield* makeApiClient
      return yield* client.getStudySessionApiV1StudySessionsSessionIdGet(
        sessionId,
      )
    }),
  ).pipe(Atom.keepAlive),
)

export const listStudySessionsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      if (!projectId) return []
      const response =
        yield* client.listStudySessionsApiV1ProjectsProjectIdStudySessionsGet(
          projectId,
        )
      return response
    }),
  ).pipe(Atom.keepAlive),
)
