import {
  DocumentIdSchema,
  ProjectIdSchema,
  type DocumentId,
} from '@/data-acess/shared'
import { usageAtom } from '@/data-acess/usage'
import type { DocumentDto } from '@/integrations/api'
import { ApiClientService } from '@/integrations/api/http'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { withToast } from '@/lib/with-toast'
import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Data, Effect, Layer, Schema } from 'effect'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

type DocumentsAction = Data.TaggedEnum<{
  Del: { readonly documentId: DocumentId }
  Update: {
    readonly document: Result.Result<DocumentDto>
  }
}>
const DocumentsAction = Data.taggedEnum<DocumentsAction>()

export const documentsRemoteAtom = Atom.family((projectId: string) =>
  runtime.atom(
    Effect.fn(function* () {
      const { apiClient } = yield* ApiClientService

      const parsedProjectId = yield* Schema.decode(ProjectIdSchema)(projectId)

      return yield* apiClient.listDocumentsApiV1ProjectsProjectIdDocumentsGet(
        parsedProjectId,
      )
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

export const documentAtom = Atom.family((input: string) => {
  const [projectId, documentId] = input.split(':')

  return Atom.make(
    Effect.fn(function* () {
      const { apiClient } = yield* ApiClientService

      const parsed = yield* Schema.decode(
        Schema.Struct({
          projectId: ProjectIdSchema,
          documentId: DocumentIdSchema,
        }),
      )({ projectId, documentId })

      return yield* apiClient.getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet(
        parsed.projectId,
        parsed.documentId,
      )
    })().pipe(Effect.provide(ApiClientService.Default)),
  )
})

export const uploadDocumentAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; files: Array<Blob> }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService

    const parsedProjectId = yield* Schema.decode(ProjectIdSchema)(
      input.projectId,
    )

    yield* apiClient.uploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost(
      parsedProjectId,
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

      const parsed = yield* Schema.decode(
        Schema.Struct({
          projectId: ProjectIdSchema,
          documentId: DocumentIdSchema,
        }),
      )(input)

      yield* apiClient.deleteDocumentApiV1ProjectsProjectIdDocumentsDocumentIdDelete(
        parsed.projectId,
        parsed.documentId,
      )

      registry.set(
        documentsAtom(parsed.projectId),
        DocumentsAction.Del({ documentId: parsed.documentId }),
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

    const parsed = yield* Schema.decode(
      Schema.Struct({
        projectId: ProjectIdSchema,
        documentId: DocumentIdSchema,
      }),
    )(input)

    // Fetch the latest document data
    const document =
      yield* apiClient.getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet(
        parsed.projectId,
        parsed.documentId,
      )

    // Update the document in the documents list atom
    registry.set(
      documentsAtom(parsed.projectId),
      DocumentsAction.Update({
        document: Result.success(document),
      }),
    )
  }),
)

export const documentPreviewAtom = Atom.family((input: string) => {
  const [projectId, documentId] = input.split(':')
  return runtime.atom(
    Effect.fn(function* () {
      const { httpClient } = yield* ApiClientService

      const parsed = yield* Schema.decode(
        Schema.Struct({
          projectId: ProjectIdSchema,
          documentId: DocumentIdSchema,
        }),
      )({ projectId, documentId })

      const response = yield* httpClient.get(
        `/api/v1/projects/${parsed.projectId}/documents/${parsed.documentId}/preview`,
      )
      const json = yield* response.json

      return json as { url: string }
    }),
  )
})
