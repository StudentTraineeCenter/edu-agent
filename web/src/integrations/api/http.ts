import * as HttpClientRequest from '@effect/platform/HttpClientRequest'
import * as HttpClient from '@effect/platform/HttpClient'
import * as FetchHttpClient from '@effect/platform/FetchHttpClient'
import * as Effect from 'effect/Effect'
import { getAccessTokenEffect } from '@/lib/supabase'
import * as ApiClient from '@/integrations/api/client'

export const makeHttpClient = Effect.gen(function* () {
  const token = yield* getAccessTokenEffect
  const client = yield* HttpClient.HttpClient

  return client.pipe(
    HttpClient.mapRequest((r) =>
      r.pipe(
        HttpClientRequest.setHeaders({
          Authorization: `Bearer ${token}`,
        }),
        HttpClientRequest.prependUrl(
          import.meta.env.VITE_SERVER_URL ?? 'http://localhost:8000',
        ),
      ),
    ),
  )
}).pipe(Effect.provide(FetchHttpClient.layer))

export const makeApiClient = Effect.gen(function* () {
  const httpClient = yield* makeHttpClient
  const token = yield* getAccessTokenEffect
  return ApiClient.make(httpClient, {
    transformClient: (c) =>
      Effect.succeed(
        c.pipe(
          HttpClient.mapRequest((r) =>
            r.pipe(
              HttpClientRequest.setHeaders({
                Authorization: `Bearer ${token}`,
              }),
            ),
          ),
        ),
      ),
  })
})
