import { createApiClient } from '@/integrations/api'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'

export const useFlashcardGroupsQuery = (projectId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: ['flashcard-groups', projectId],
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
            return data
        },
    })
}

export const useFlashcardGroupQuery = (groupId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: ['flashcard-group', groupId],
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/flashcards/{group_id}', {
                params: { path: { group_id: groupId } },
            })
            return data
        },
    })
}

export const useFlashcardsQuery = (groupId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: ['flashcards', groupId],
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
            return data
        },
    })
}

