import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Layer } from 'effect'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { usageAtom } from './usage'
import type { DocumentDto } from '@/integrations/api'
import { ApiClientService } from '@/integrations/api/http'
import { getAccessTokenEffect } from '@/lib/supabase'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { withToast } from '@/lib/with-toast'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

type DocumentsAction = Data.TaggedEnum<{
  Del: { readonly documentId: string }
  Update: {
    readonly document: Result.Result<DocumentDto>
  }
}>
const DocumentsAction = Data.taggedEnum<DocumentsAction>()

export const documentsRemoteAtom = Atom.family((projectId: string) =>
  runtime.atom(
    Effect.fn(function* () {
      const { apiClient } = yield* ApiClientService
      const resp =
        yield* apiClient.listDocumentsApiV1ProjectsProjectIdDocumentsGet(
          projectId,
        )
      return resp
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
          Update: ({ document }) => {
            if (!Result.isSuccess(document)) return result.value
            return result.value.map((d) =>
              d.id === document.value.id ? document.value : d,
            )
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
        const { apiClient } = yield* ApiClientService
        return yield* apiClient.getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet(
          input.projectId,
          input.documentId,
        )
      })().pipe(Effect.provide(ApiClientService.Default)),
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
  Effect.fn(function* (input: { projectId: string; files: Array<Blob> }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService

    yield* apiClient.uploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost(
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
      const { apiClient } = yield* ApiClientService
      yield* apiClient.deleteDocumentApiV1ProjectsProjectIdDocumentsDocumentIdDelete(
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

export const refreshDocumentsAtom = runtime.fn(
  Effect.fn(function* (projectId: string) {
    const registry = yield* Registry.AtomRegistry
    registry.refresh(documentsRemoteAtom(projectId))
  }),
)

export const refreshDocumentAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; documentId: string }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService

    // Fetch the latest document data
    const document =
      yield* apiClient.getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet(
        input.projectId,
        input.documentId,
      )

    // Update the document in the documents list atom
    registry.set(
      documentsAtom(input.projectId),
      DocumentsAction.Update({
        document: Result.success(document),
      }),
    )
  }),
)
