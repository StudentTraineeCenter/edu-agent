import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { runtime } from './runtime'

export const studyPlanAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const apiClient = yield* makeApiClient
      const studyPlan = yield* apiClient
        .getStudyPlanV1ProjectsProjectIdStudyPlansGet(projectId)
        .pipe(
          Effect.catchTag('ResponseError', (error) => {
            if (error.response.status === 404) {
              return Effect.succeed(null)
            }
            return Effect.fail(error)
          }),
        )

      return studyPlan
    }),
  ).pipe(Atom.keepAlive),
)

export const generateStudyPlanAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const studyPlan =
      yield* apiClient.generateStudyPlanV1ProjectsProjectIdStudyPlansPost(
        input.projectId,
      )
    registry.refresh(studyPlanAtom(input.projectId))
    return studyPlan
  }),
)
