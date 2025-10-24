import { createApiClient } from '@/integrations/api'
import { useQuery, type QueryKey } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'

export const FLASHCARD_GROUPS_QUERY_KEY = (projectId: string): QueryKey => ['project', projectId, 'flashcard-groups']

export const useFlashcardGroupsQuery = (projectId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: FLASHCARD_GROUPS_QUERY_KEY(projectId),
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/flashcards', {
                params: {
                    query: {
                        project_id: projectId,
                    },
                },
            })
            if (!data) throw new Error('Failed to get flashcard groups')
            return data
        },
    })
}

export const FLASHCARD_GROUP_QUERY_KEY = (groupId: string): QueryKey => ['flashcard-group', groupId]

export const useFlashcardGroupQuery = (groupId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: FLASHCARD_GROUP_QUERY_KEY(groupId),
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/flashcards/{group_id}', {
                params: { path: { group_id: groupId } },
            })
            if (!data) throw new Error('Failed to get flashcard group')
            return data
        },
    })
}

export const FLASHCARDS_QUERY_KEY = (groupId: string): QueryKey => ['flashcards', groupId]

export const useFlashcardsQuery = (groupId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: FLASHCARDS_QUERY_KEY(groupId),
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET(
                '/v1/flashcards/{group_id}/flashcards',
                {
                    params: { path: { group_id: groupId } },
                },
            )
            if (!data) throw new Error('Failed to get flashcards')
            return data
        },
    })
}

