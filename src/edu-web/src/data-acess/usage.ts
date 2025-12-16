import { Data, Effect, Layer } from 'effect'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { ApiClientService } from '@/integrations/api'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

export class UsageLimitExceededError extends Data.TaggedError(
  'UsageLimitExceededError',
)<{
  readonly message: string
}> {}

export const usageAtom = runtime.atom(
  Effect.fn(function* () {
    const { apiClient } = yield* ApiClientService
    const resp = yield* apiClient.getUsageApiV1UsageGet()
    return resp
  }),
)
