import { ApiClientService } from '@/integrations/api/http'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { NetworkMonitor } from '@/lib/network-monitor'
import { Atom, Registry } from '@effect-atom/atom-react'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Effect, Layer, Schema } from 'effect'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    NetworkMonitor.Default,
    ApiClientService.Default,
  ),
)

export const latestStudyPlanRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const { apiClient } = yield* ApiClientService
        const resp =
          yield* apiClient.getLatestStudyPlanApiV1ProjectsProjectIdStudyPlansLatestGet(
            projectId,
          )
        return resp
      }),
    )
    .pipe(Atom.keepAlive),
)

export const studyPlansHistoryRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const { apiClient } = yield* ApiClientService
        const resp =
          yield* apiClient.listStudyPlansApiV1ProjectsProjectIdStudyPlansGet(
            projectId,
          )
        return resp
      }),
    )
    .pipe(Atom.keepAlive),
)

export class StudyResource extends Schema.Class<StudyResource>('StudyResource')(
  {
    id: Schema.String,
    parent_id: Schema.NullOr(Schema.String),
    type: Schema.Literal('quiz', 'flashcard'),
    title: Schema.String,
    description: Schema.NullOr(Schema.String),
  },
) {}

export const generateStudyPlanAtom = runtime.fn(
  Effect.fn(function* (projectId: string) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService

    const resp =
      yield* apiClient.generateStudyPlanApiV1ProjectsProjectIdStudyPlansGeneratePost(
        projectId,
      )

    // Refresh related atoms
    registry.refresh(latestStudyPlanRemoteAtom(projectId))
    registry.refresh(studyPlansHistoryRemoteAtom(projectId))

    return resp
  }),
)
