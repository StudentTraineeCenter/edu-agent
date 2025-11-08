import { Atom } from '@effect-atom/atom-react'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Data } from 'effect'

export const runtime = Atom.runtime(BrowserKeyValueStore.layerLocalStorage)

export class UsageLimitExceededError extends Data.TaggedError(
  'UsageLimitExceededError',
)<{
  readonly message: string
}> {}
