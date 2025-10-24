import { useQuery } from '@tanstack/react-query'
import { createApiClient } from '@/integrations/api'
import { useAuth } from '@/hooks/use-auth'

export const ME_QUERY_KEY = () => ['me']

export const useMeQuery = () => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ME_QUERY_KEY(),
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET('/v1/auth/me')
      if (!data) throw new Error('Failed to get me')
      return data
    },
  })
}

export const useProfilePhotoQuery = () => {
  const { getProfilePhoto, account } = useAuth()

  return useQuery({
    queryKey: ['profile-photo', account?.homeAccountId],
    queryFn: getProfilePhoto,
    enabled: !!account,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}