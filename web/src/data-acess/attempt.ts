import { Data, Effect } from 'effect'
import { makeApiClient } from '@/integrations/api/http'
import type {
  AttemptDto,
  CreateAttemptBatchRequest,
  CreateAttemptRequest,
} from '@/integrations/api'
import { runtime } from './runtime'
import { Atom, Registry, Result } from '@effect-atom/atom-react'

type AttemptsAction = Data.TaggedEnum<{
  List: { readonly projectId: string }
  Create: { readonly attempt: AttemptDto }
  CreateBatch: { readonly attempts: ReadonlyArray<AttemptDto> }
}>
const AttemptsAction = Data.taggedEnum<AttemptsAction>()

export const attemptsRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const apiClient = yield* makeApiClient
        const resp = yield* apiClient.listAttemptsV1AttemptsGet({
          project_id: projectId,
        })
        return resp.attempts
      }),
    )
    .pipe(Atom.keepAlive),
)

export const attemptsAtom = Atom.family((projectId: string) =>
  Object.assign(
    Atom.writable(
      (get: Atom.Context) => get(attemptsRemoteAtom(projectId)),
      (ctx, action: AttemptsAction) => {
        const result = ctx.get(attemptsAtom(projectId))
        if (!Result.isSuccess(result)) return

        const update = AttemptsAction.$match(action, {
          List: () => {
            return result.value
          },
          Create: ({ attempt }) => {
            return {
              ...result.value,
              attempts: [...result.value, attempt],
            }
          },
          CreateBatch: ({ attempts }) => {
            return {
              ...result.value,
              attempts: [...result.value, ...attempts],
            }
          },
        })

        ctx.setSelf(Result.success(update))
      },
    ),
    {
      remote: attemptsRemoteAtom(projectId),
    },
  ),
)

export const submitAttemptAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof CreateAttemptRequest.Encoded & { projectId: string },
  ) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const resp = yield* apiClient.createAttemptV1AttemptsPost({
      params: { project_id: input.projectId },
      payload: input,
    })

    registry.set(
      attemptsAtom(input.projectId),
      AttemptsAction.Create({ attempt: resp.attempt }),
    )

    registry.refresh(attemptsRemoteAtom(input.projectId))

    return resp
  }),
)

export const submitAttemptsBatchAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof CreateAttemptBatchRequest.Encoded & { projectId: string },
  ) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const resp = yield* apiClient.createAttemptsBatchV1AttemptsBatchPost({
      params: { project_id: input.projectId },
      payload: input,
    })
    registry.set(
      attemptsAtom(input.projectId),
      AttemptsAction.CreateBatch({
        attempts: resp.attempts,
      }),
    )
    registry.refresh(attemptsRemoteAtom(input.projectId))
    return resp.attempts
  }),
)
