import { useAuth } from '@/hooks/use-auth'
import { createApiClient } from '@/integrations/api'
import { useMutation, useQuery } from '@tanstack/react-query'

export const useProjectsQuery = () => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET('/v1/projects')
      return data
    },
  })
}

export const useProjectQuery = (projectId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET(`/v1/projects/{project_id}`, {
        params: {
          path: {
            project_id: projectId,
          },
        },
      })
      return data
    },
  })
}

export const useCreateProjectMutation = (options?: {
  onSuccess?: () => void
}) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    mutationFn: async (payload: {
      name: string
      description?: string | null
      language_code?: string | null
    }) => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.POST('/v1/projects', {
        body: {
          name: payload.name,
          description: payload.description,
          language_code: payload.language_code ?? 'en',
        },
      })
      return data
    },
    onSuccess: options?.onSuccess,
  })
}
