import { useMsal, useIsAuthenticated, useAccount } from '@azure/msal-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { loginRequest } from '@/lib/msal-config'

export const useAuth = () => {
  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = useAccount(accounts[0])
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    mutationFn: async () => {
      await instance.loginRedirect(loginRequest)
    },
    onError: (error) => {
      console.error('Login failed:', error)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await instance.logoutRedirect({
        postLogoutRedirectUri: '/',
      })
    },
    onSuccess: () => {
      queryClient.clear()
    },
    onError: (error) => {
      console.error('Logout failed:', error)
    },
  })

  const getAccessToken = async () => {
    if (!account) return null

    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account: account,
      })
      return response.accessToken
    } catch (error) {
      console.error('Failed to acquire token:', error)
      return null
    }
  }

  const getProfilePhoto = async (): Promise<string | null> => {
    const token = await getAccessToken()
    if (!token) return null

    try {
      const response = await fetch('https://graph.microsoft.com/v1.0/me/photo/$value', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) return null

      const blob = await response.blob()
      return URL.createObjectURL(blob)
    } catch (error) {
      console.error('Failed to fetch profile photo:', error)
      return null
    }
  }

  return {
    isAuthenticated,
    account,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    getAccessToken,
    getProfilePhoto,
    isLoading: loginMutation.isPending || logoutMutation.isPending,
    loginError: loginMutation.error,
    logoutError: logoutMutation.error,
    user: account
      ? {
        id: account.homeAccountId,
        name: account.name || '',
        email: account.username || '',
      }
      : null,
  }
}
