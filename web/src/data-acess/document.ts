import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Data, Effect } from 'effect'
import { runtime } from './runtime'
import { usageAtom } from './usage'

type DocumentsAction = Data.TaggedEnum<{
  Del: { readonly documentId: string }
}>
const DocumentsAction = Data.taggedEnum<DocumentsAction>()

export const documentsRemoteAtom = Atom.family((projectId: string) =>
  runtime.atom(
    Effect.fn(function* () {
      const client = yield* makeApiClient
      const resp = yield* client.listDocumentsV1DocumentsGet({
        project_id: projectId,
      })
      return resp.data
    }),
  ),
)

export const documentsAtom = Atom.family((projectId: string) =>
  Object.assign(
    Atom.writable(
      (get: Atom.Context) => get(documentsRemoteAtom(projectId)),
      (ctx, action: DocumentsAction) => {
        const result = ctx.get(documentsAtom(projectId))
        if (!Result.isSuccess(result)) return

        const update = DocumentsAction.$match(action, {
          Del: ({ documentId }) => {
            return result.value.filter((d) => d.id !== documentId)
          },
        })

        ctx.setSelf(Result.success(update))
      },
    ),
    {
      remote: documentsRemoteAtom(projectId),
    },
  ),
)

export const indexedDocumentsAtom = Atom.family((projectId: string) =>
  Atom.make((get) =>
    get(documentsRemoteAtom(projectId)).pipe(
      Result.map((d) => d.filter((d) => d.status === 'indexed')),
    ),
  ),
)

export const documentAtom = Atom.family((documentId: string) =>
  Atom.make(
    Effect.fn(function* () {
      const client = yield* makeApiClient
      return yield* client.getDocumentV1DocumentsDocumentIdGet(documentId)
    }),
  ),
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

export const uploadDocumentAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; files: Blob[] }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient

    yield* client.uploadDocumentV1DocumentsUploadPost({
      params: { project_id: input.projectId },
      payload: { files: input.files },
    })

    registry.refresh(documentsRemoteAtom(input.projectId))
    registry.refresh(usageAtom)
  }),
)

export const deleteDocumentAtom = runtime.fn(
  Effect.fn(function* (input: { documentId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteDocumentV1DocumentsDocumentIdDelete(input.documentId)

    registry.set(
      documentsAtom(input.projectId),
      DocumentsAction.Del({ documentId: input.documentId }),
    )
  }),
)
