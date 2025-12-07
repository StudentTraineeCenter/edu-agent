import { Effect } from 'effect'
import { supabase } from './supabase'

export const getAccessToken = async (): Promise<string | null> => {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

export const getAccessTokenEffect = Effect.promise(() => getAccessToken())
