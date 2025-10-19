import { createApiClient } from '@/integrations/api'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'

export const useQuizzesQuery = (projectId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: ['quizzes', projectId],
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/quizzes', {
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

export const useQuizQuery = (quizId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: ['quiz', quizId],
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/quizzes/{quiz_id}', {
                params: { path: { quiz_id: quizId } },
            })
            return data
        },
    })
}

export const useQuizQuestionsQuery = (quizId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: ['quiz-questions', quizId],
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/quizzes/{quiz_id}/questions', {
                params: { path: { quiz_id: quizId } },
            })
            return data
        },
    })
}

