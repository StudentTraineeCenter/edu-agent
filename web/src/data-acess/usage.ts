import { Data, Effect } from 'effect'
import { makeApiClient } from '@/integrations/api'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'

const runtime = makeAtomRuntime(BrowserKeyValueStore.layerLocalStorage)

export class UsageLimitExceededError extends Data.TaggedError(
  'UsageLimitExceededError',
)<{
  readonly message: string
}> {}

export const usageAtom = runtime.atom(
  Effect.fn(function* () {
    const client = yield* makeApiClient
    const resp = yield* client.getUsageApiV1UsageGet()
    return resp
  }),
)
