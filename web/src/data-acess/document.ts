import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { makeApiClient } from '@/integrations/api/http'
import { Data, Effect } from 'effect'
import { getAccessTokenEffect } from '@/lib/supabase'
import { usageAtom } from './usage'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { withToast } from '@/lib/with-toast'

const runtime = makeAtomRuntime(BrowserKeyValueStore.layerLocalStorage)

type DocumentsAction = Data.TaggedEnum<{
  Del: { readonly documentId: string }
}>
const DocumentsAction = Data.taggedEnum<DocumentsAction>()

export const documentsRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const client = yield* makeApiClient
        const resp =
          yield* client.listDocumentsApiV1ProjectsProjectIdDocumentsGet(
            projectId,
          )
        return resp
      }),
    )
    .pipe(Atom.keepAlive),
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

export const documentAtom = Atom.family(
  (input: { projectId: string; documentId: string }) =>
    Atom.make(
      Effect.fn(function* () {
        const client = yield* makeApiClient
        return yield* client.getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet(
          input.projectId,
          input.documentId,
        )
      }),
    ),
)

export const documentPreviewAtom = Atom.family(
  (_input: { projectId: string; documentId: string }) =>
    Atom.make(
      Effect.fn(function* () {
        // Note: Document preview endpoints may not be available in the new API
        // const client = yield* makeApiClient
        // const preview = yield* client.getDocumentPreview(...)
        const preview = {
          preview_url: 'http://localhost:8000/v1/documents/1/stream',
          content_type: 'application/pdf',
        }

        // Construct full URL for streaming endpoint
        const serverUrl =
          import.meta.env.VITE_SERVER_URL ?? 'http://localhost:8000'
        const streamUrl = preview.preview_url.startsWith('http')
          ? preview.preview_url
          : `${serverUrl}${preview.preview_url}`

        // Fetch the stream with auth and create blob URL
        const token = yield* getAccessTokenEffect
        if (!token) {
          throw new Error('No access token available')
        }

        const response = yield* Effect.promise(() =>
          fetch(streamUrl, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }),
        )

        if (!response.ok) {
          return yield* Effect.fail(
            new Error(
              `Failed to fetch document stream: ${response.statusText}`,
            ),
          )
        }

        const blob = yield* Effect.promise(() => response.blob())
        const blobUrl = URL.createObjectURL(blob)

        return {
          preview_url: blobUrl,
          content_type: preview.content_type,
        }
      }),
    ).pipe(Atom.keepAlive),
)

export const uploadDocumentAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; files: Blob[] }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient

    yield* client.uploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost(
      input.projectId,
      {
        files: input.files,
      },
    )

    registry.refresh(documentsRemoteAtom(input.projectId))
    registry.refresh(usageAtom)
  }),
)

export const deleteDocumentAtom = runtime.fn(
  Effect.fn(
    function* (input: { documentId: string; projectId: string }) {
      const registry = yield* Registry.AtomRegistry
      const client = yield* makeApiClient
      yield* client.deleteDocumentApiV1ProjectsProjectIdDocumentsDocumentIdDelete(
        input.projectId,
        input.documentId,
      )

      registry.set(
        documentsAtom(input.projectId),
        DocumentsAction.Del({ documentId: input.documentId }),
      )
    },
    withToast({
      onWaiting: () => 'Deleting document...',
      onSuccess: 'Document deleted',
      onFailure: 'Failed to delete document',
    }),
  ),
)
