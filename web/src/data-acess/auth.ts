import { Atom } from '@effect-atom/atom-react'
import { Effect } from 'effect'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'

export const ME_QUERY_KEY = () => ['me']

export const meAtom = Atom.make(
  Effect.gen(function* () {
    const client = yield* makeApiClient
    return yield* client.getCurrentUserInfoV1AuthMeGet()
  }),
).pipe(Atom.keepAlive)

export const profilePhotoAtom = Atom.make(
  Effect.gen(function* () {
    const httpClient = yield* makeHttpClient

    const resp = yield* httpClient.get(
      'https://graph.microsoft.com/v1.0/me/photo/$value',
    )
    const buffer = yield* resp.arrayBuffer
    return URL.createObjectURL(new Blob([buffer]))
  }),
).pipe(Atom.keepAlive)
