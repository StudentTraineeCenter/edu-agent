import { useQuery } from '@tanstack/react-query'
import { createApiClient } from '@/integrations/api'
import { useAuth } from '@/hooks/use-auth'

export const useMeQuery = () => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET('/v1/auth/me')
      return data
    },
  })
}
