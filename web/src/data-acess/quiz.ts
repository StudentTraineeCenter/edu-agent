import { createApiClient } from '@/integrations/api'
import { useQuery, type QueryKey } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'

export const QUIZZES_QUERY_KEY = (projectId: string): QueryKey => ['project', projectId, 'quizzes']

export const useQuizzesQuery = (projectId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: QUIZZES_QUERY_KEY(projectId),
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
            if (!data) throw new Error('Failed to get quizzes')
            return data
        },
    })
}

export const QUIZ_QUERY_KEY = (quizId: string): QueryKey => ['quiz', quizId]

export const useQuizQuery = (quizId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: QUIZ_QUERY_KEY(quizId),
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/quizzes/{quiz_id}', {
                params: { path: { quiz_id: quizId } },
            })
            if (!data) throw new Error('Failed to get quiz')
            return data
        },
    })
}

export const QUIZ_QUESTIONS_QUERY_KEY = (quizId: string): QueryKey => ['quiz-questions', quizId]

export const useQuizQuestionsQuery = (quizId: string) => {
    const { getAccessToken } = useAuth()

    return useQuery({
        queryKey: QUIZ_QUESTIONS_QUERY_KEY(quizId),
        queryFn: async () => {
            const token = await getAccessToken()
            if (!token) throw new Error('No token')

            const client = createApiClient(token)

            const { data } = await client.GET('/v1/quizzes/{quiz_id}/questions', {
                params: { path: { quiz_id: quizId } },
            })
            if (!data) throw new Error('Failed to get quiz questions')
            return data
        },
    })
}

