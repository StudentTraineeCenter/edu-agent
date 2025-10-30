import { Atom } from '@effect-atom/atom-react'
import { BrowserKeyValueStore } from '@effect/platform-browser'

export const runtime = Atom.runtime(BrowserKeyValueStore.layerLocalStorage)
