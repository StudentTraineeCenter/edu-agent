import { Data, Effect } from 'effect'
import { makeApiClient } from '@/integrations/api/http'
import type {
  PracticeRecordDto,
  CreatePracticeRecordBatchRequest,
  CreatePracticeRecordRequest,
} from '@/integrations/api'
import { runtime } from './runtime'
import { Atom, Registry, Result } from '@effect-atom/atom-react'

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
        const apiClient = yield* makeApiClient
        const resp = yield* apiClient.listPracticeRecordsV1PracticeRecordsGet({
          project_id: projectId,
        })
        return resp.data
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
    input: typeof CreatePracticeRecordRequest.Encoded & { projectId: string },
  ) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const resp = yield* apiClient.createPracticeRecordV1PracticeRecordsPost({
      params: { project_id: input.projectId },
      payload: input,
    })

    registry.set(
      practiceRecordsAtom(input.projectId),
      PracticeRecordsAction.Create({ practiceRecord: resp.practice_record }),
    )

    registry.refresh(practiceRecordsRemoteAtom(input.projectId))

    return resp
  }),
)

export const submitPracticeRecordsBatchAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof CreatePracticeRecordBatchRequest.Encoded & {
      projectId: string
    },
  ) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const resp =
      yield* apiClient.createPracticeRecordsBatchV1PracticeRecordsBatchPost({
        params: { project_id: input.projectId },
        payload: input,
      })
    registry.set(
      practiceRecordsAtom(input.projectId),
      PracticeRecordsAction.CreateBatch({
        practiceRecords: resp.data,
      }),
    )
    registry.refresh(practiceRecordsRemoteAtom(input.projectId))
    return resp.data
  }),
)
