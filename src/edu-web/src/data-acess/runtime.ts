import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Layer } from 'effect'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { ApiClientService } from '@/integrations/api/http'

export const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)
