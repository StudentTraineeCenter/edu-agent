import { useContext } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { SupabaseContext } from '@/providers/supabase-provider'
import { supabase } from '@/lib/supabase'

export const useAuth = () => {
  const { session, user, loading } = useContext(SupabaseContext)
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    mutationFn: async ({
      email,
      password,
    }: {
      email: string
      password?: string
    }) => {
      if (password) {
        // Email/password login
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) throw error
        return data
      } else {
        // Magic link login
        const { data, error } = await supabase.auth.signInWithOtp({
          email,
          options: {
            emailRedirectTo: window.location.origin,
          },
        })
        if (error) throw error
        return data
      }
    },
    onError: (error) => {
      console.error('Login failed:', error)
    },
  })

  const magicLinkMutation = useMutation({
    mutationFn: async (email: string) => {
      const { data, error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: window.location.origin,
        },
      })
      if (error) throw error
      return data
    },
    onError: (error) => {
      console.error('Magic link failed:', error)
    },
  })

  const signUpMutation = useMutation({
    mutationFn: async ({
      email,
      password,
    }: {
      email: string
      password: string
    }) => {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: window.location.origin,
        },
      })
      if (error) throw error
      return data
    },
    onError: (error) => {
      console.error('Sign up failed:', error)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    },
    onSuccess: () => {
      queryClient.clear()
    },
    onError: (error) => {
      console.error('Logout failed:', error)
    },
  })

  const getAccessToken = async () => {
    if (!session) return null
    return session.access_token
  }

  return {
    isAuthenticated: !!session && !!user,
    session,
    user,
    login: loginMutation.mutate,
    signUp: signUpMutation.mutate,
    sendMagicLink: magicLinkMutation.mutate,
    logout: logoutMutation.mutate,
    getAccessToken,
    isLoading:
      loading ||
      loginMutation.isPending ||
      logoutMutation.isPending ||
      signUpMutation.isPending ||
      magicLinkMutation.isPending,
    loginError: loginMutation.error,
    logoutError: logoutMutation.error,
    signUpError: signUpMutation.error,
    magicLinkError: magicLinkMutation.error,
  }
}
