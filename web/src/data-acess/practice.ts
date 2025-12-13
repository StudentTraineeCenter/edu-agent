import { Data, Effect, Layer } from 'effect'
import { ApiClientService } from '@/integrations/api/http'
import {
  PracticeRecordDto,
  PracticeRecordCreate,
  PracticeRecordBatchCreate,
} from '@/integrations/api/client'
import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

type PracticeRecordsAction = Data.TaggedEnum<{
  List: { readonly projectId: string }
  Create: { readonly practiceRecord: PracticeRecordDto }
  CreateBatch: { readonly practiceRecords: ReadonlyArray<PracticeRecordDto> }
}>
const PracticeRecordsAction = Data.taggedEnum<PracticeRecordsAction>()

export const practiceRecordsRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const { apiClient } = yield* ApiClientService
        const resp =
          yield* apiClient.listPracticeRecordsApiV1ProjectsProjectIdPracticeRecordsGet(
            projectId,
          )
        return resp
      }),
    )
    .pipe(Atom.keepAlive),
)

export const practiceRecordsAtom = Atom.family((projectId: string) =>
  Object.assign(
    Atom.writable(
      (get: Atom.Context) => get(practiceRecordsRemoteAtom(projectId)),
      (ctx, action: PracticeRecordsAction) => {
        const result = ctx.get(practiceRecordsAtom(projectId))
        if (!Result.isSuccess(result)) return

        const update = PracticeRecordsAction.$match(action, {
          List: () => {
            return result.value
          },
          Create: ({ practiceRecord }) => {
            return [...result.value, practiceRecord]
          },
          CreateBatch: ({ practiceRecords }) => {
            return [...result.value, ...practiceRecords]
          },
        })

        ctx.setSelf(Result.success(update))
      },
    ),
    {
      remote: practiceRecordsRemoteAtom(projectId),
    },
  ),
)

export const submitPracticeRecordAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof PracticeRecordCreate.Encoded & { projectId: string },
  ) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.createPracticeRecordApiV1ProjectsProjectIdPracticeRecordsPost(
        input.projectId,
        input,
      )

    registry.set(
      practiceRecordsAtom(input.projectId),
      PracticeRecordsAction.Create({ practiceRecord: resp }),
    )

    registry.refresh(practiceRecordsRemoteAtom(input.projectId))

    return resp
  }),
)

export const submitPracticeRecordsBatchAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof PracticeRecordBatchCreate.Encoded & {
      projectId: string
    },
  ) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.createPracticeRecordsBatchApiV1ProjectsProjectIdPracticeRecordsBatchPost(
        input.projectId,
        input,
      )

    registry.set(
      practiceRecordsAtom(input.projectId),
      PracticeRecordsAction.CreateBatch({
        practiceRecords: resp,
      }),
    )
    registry.refresh(practiceRecordsRemoteAtom(input.projectId))
    return resp
  }),
)
