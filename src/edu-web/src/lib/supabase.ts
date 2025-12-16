import { createClient } from '@supabase/supabase-js'
import { Effect } from 'effect'
import { env } from '@/env'

export const supabase = createClient(
  env.VITE_SUPABASE_URL,
  env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  },
)

export const getAccessTokenEffect = Effect.promise(async () => {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  return session?.access_token ?? null
})
