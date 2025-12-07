import React, { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import type { Session, User } from '@supabase/supabase-js'

interface SupabaseContextType {
  session: Session | null
  user: User | null
  loading: boolean
}

export const SupabaseContext = React.createContext<SupabaseContextType>({
  session: null,
  user: null,
  loading: true,
})

export const SupabaseProvider = ({
  children,
}: {
  children: React.ReactNode
}) => {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  return (
    <SupabaseContext.Provider value={{ session, user, loading }}>
      {children}
    </SupabaseContext.Provider>
  )
}
