import { useAuth } from '@/hooks/use-auth'
import { createApiClient, type Project, type ProjectCreateRequest } from '@/integrations/api'
import { useMutation, useQuery, type QueryKey } from '@tanstack/react-query'
import type { MutationOptions } from '@/data-acess/utils'

export const PROJECTS_QUERY_KEY = (): QueryKey => ['projects']

export const useProjectsQuery = () => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: PROJECTS_QUERY_KEY(),
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET('/v1/projects')
      if (!data) throw new Error('Failed to get projects')
      return data
    },
  })
}

export const PROJECT_QUERY_KEY = (projectId: string): QueryKey => ['project', projectId]

export const useProjectQuery = (projectId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: PROJECT_QUERY_KEY(projectId),
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
      if (!data) throw new Error('Failed to get project')
      return data
    },
  })
}

export const CREATE_PROJECT_MUTATION_KEY = (): QueryKey => ['create-project']

export const useCreateProjectMutation = (options?: MutationOptions<Project, ProjectCreateRequest>) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    ...options,
    mutationFn: async (variables) => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.POST('/v1/projects', {
        body: {
          name: variables.name,
          description: variables.description,
          language_code: variables.language_code ?? 'cs',
        },
      })
      if (!data) throw new Error('Failed to create project')
      return data
    },
  })
}
