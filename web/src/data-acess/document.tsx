import { baseUrl, createApiClient } from '@/integrations/api'
import { useQuery } from '@tanstack/react-query'
import { FileIcon } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'

export const getIcon = (fileType: string) => {
  switch (fileType) {
    case 'pdf':
      return <FileIcon />
  }
}

export const useDocumentsQuery = (projectId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ['documents', projectId],
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
      return data
    },
  })
}

export const useDocumentQuery = (documentId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ['document', documentId],
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET('/v1/documents/{document_id}', {
        params: { path: { document_id: documentId } },
      })
      return data
    },
  })
}

export const useDocumentPreviewQuery = (
  documentId: string | null | undefined,
  page?: number | null,
) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    enabled: Boolean(documentId),
    queryKey: ['document', documentId, 'preview', page ?? null],
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
