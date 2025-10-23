import { baseUrl, createApiClient } from '@/integrations/api'
import { useQuery, type QueryKey } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'

export const DOCUMENTS_QUERY_KEY = (projectId: string): QueryKey => ['project', projectId, 'documents']

export const useDocumentsQuery = (projectId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: DOCUMENTS_QUERY_KEY(projectId),
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET(`/v1/documents`, {
        params: {
          query: {
            project_id: projectId,
          },
        },
      })
      if (!data) throw new Error('Failed to get documents')
      return data
    },
  })
}

export const DOCUMENT_QUERY_KEY = (documentId: string): QueryKey => ['document', documentId]

export const useDocumentQuery = (documentId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: DOCUMENT_QUERY_KEY(documentId),
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET('/v1/documents/{document_id}', {
        params: { path: { document_id: documentId } },
      })
      if (!data) throw new Error('Failed to get document')
      return data
    },
  })
}

export const DOCUMENT_PREVIEW_QUERY_KEY = (documentId: string, page?: number | null): QueryKey => ['document', documentId, 'preview', page ?? null]

export const useDocumentPreviewQuery = (
  documentId: string | null | undefined,
  page?: number | null,
) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    enabled: Boolean(documentId),
    queryKey: DOCUMENT_PREVIEW_QUERY_KEY(documentId ?? '', page ?? null),
    queryFn: async () => {
      if (!documentId) return null
      const previewUrl = new URL(
        `${baseUrl}/v1/documents/${documentId}/preview`,
      )
      if (typeof page === 'number' && !Number.isNaN(page)) {
        previewUrl.searchParams.set('page', String(page))
      }

      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const res = await fetch(previewUrl.toString(), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (!res.ok) throw new Error(`Failed to load preview (${res.status})`)
      if (!res.body) throw new Error('Failed to load preview')
      const blob = await res.blob()
      const objectUrl = URL.createObjectURL(blob)
      return objectUrl
    },
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: false,
    meta: {
      // cleanup the blob URL when query is removed from cache
      onRemove: (data: unknown) => {
        if (typeof data === 'string') URL.revokeObjectURL(data)
      },
    },
  })
}
