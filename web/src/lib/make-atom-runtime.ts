import { Atom } from '@effect-atom/atom-react'
import { Layer, Logger, LogLevel } from 'effect'
import { NetworkMonitor } from './network-monitor'
import { ApiClientService } from '@/integrations/api'

export const makeAtomRuntime = Atom.context({ memoMap: Atom.defaultMemoMap })

makeAtomRuntime.addGlobalLayer(
  Layer.mergeAll(
    Layer.provideMerge(
      Logger.pretty,
      Logger.minimumLogLevel(
        import.meta.env.NODE_ENV === 'development'
          ? LogLevel.Debug
          : LogLevel.Info,
      ),
    ),
    ApiClientService.Default,
    NetworkMonitor.Default,
  ),
)
