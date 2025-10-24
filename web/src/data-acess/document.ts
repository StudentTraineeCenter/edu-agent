import { Atom } from '@effect-atom/atom-react'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Effect } from 'effect'

export const documentsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      const resp = yield* client.listDocumentsV1DocumentsGet({
        project_id: projectId,
      })
      return resp.data
    }),
  ).pipe(Atom.keepAlive),
)

export const documentAtom = Atom.family((documentId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.getDocumentV1DocumentsDocumentIdGet(documentId)
    }),
  ).pipe(Atom.keepAlive),
)
export const documentPreviewAtom = Atom.family((documentId: string) =>
  Atom.make(
    Effect.fn(function* (get: Atom.FnContext) {
      const httpClient = yield* makeHttpClient
      const resp = yield* httpClient.get(`/v1/documents/${documentId}/preview`)
      const buffer = yield* resp.arrayBuffer
      const blob = new Blob([buffer], { type: 'application/pdf' })
      const objectUrl = URL.createObjectURL(blob)
      get.addFinalizer(() => {
        URL.revokeObjectURL(objectUrl)
      })
      return objectUrl
    }),
  ).pipe(Atom.keepAlive),
)
