import { Effect } from 'effect'
import { runtime } from './runtime'
import { makeApiClient } from '@/integrations/api'

export const usageAtom = runtime.atom(
  Effect.fn(function* () {
    const client = yield* makeApiClient
    const resp = yield* client.getUsageApiV1UsageGet()
    return resp
  }),
)
