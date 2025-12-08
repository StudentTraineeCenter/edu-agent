import { Atom } from '@effect-atom/atom-react'
import { Effect } from 'effect'
import { makeApiClient } from '@/integrations/api/http'
import { supabase } from '@/lib/supabase'
import type { Session, User } from '@supabase/supabase-js'

export const ME_QUERY_KEY = () => ['me']

export const currentUserAtom = Atom.make(
  Effect.gen(function* () {
    const client = yield* makeApiClient
    const resp = yield* client.getCurrentUserInfoV1AuthMeGet()

    const name = resp.name?.trim() ?? resp.email?.split('@')[0] ?? 'User'

    const initials = name
      .split(' ')
      .map((n: string) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)

    return {
      ...resp,
      name,
      initials,
    }
  }),
).pipe(Atom.keepAlive)

export const authAtom: Atom.Atom<{
  session: Session | null
  user: User | null
}> = Atom.make((get) => {
  supabase.auth.getSession().then(({ data: { session } }) => {
    get.setSelf({ session, user: session?.user ?? null })
  })

  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((_event, session) => {
    get.setSelf({ session, user: session?.user ?? null })
  })

  get.addFinalizer(() => subscription.unsubscribe())

  return { session: null, user: null }
})

export const isAuthenticatedAtom = Atom.make((get) => {
  const auth = get(authAtom)
  return !!auth.session && !!auth.user
})

type SignInPayload =
  | {
      readonly type: 'password'
      readonly email: string
      readonly password: string
    }
  | { readonly type: 'magic_link'; readonly email: string }

export const signInAtom = Atom.fn(
  Effect.fn(function* (payload: SignInPayload) {
    if (payload.type === 'password') {
      yield* Effect.promise(async () => {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: payload.email,
          password: payload.password,
        })
        if (error) throw error
        return data
      })
    } else if (payload.type === 'magic_link') {
      yield* Effect.promise(async () => {
        const { data, error } = await supabase.auth.signInWithOtp({
          email: payload.email,
          options: {
            emailRedirectTo: window.location.origin,
          },
        })
        if (error) throw error
        return data
      })
    }
  }),
)

export const signUpAtom = Atom.fn(
  Effect.fn(function* (payload: { email: string; password: string }) {
    yield* Effect.promise(async () => {
      const { data, error } = await supabase.auth.signUp({
        email: payload.email,
        password: payload.password,
        options: {
          emailRedirectTo: window.location.origin,
        },
      })
      if (error) throw error
      return data
    })
  }),
)

export const signOutAtom = Atom.fn(
  Effect.fn(function* () {
    yield* Effect.promise(async () => {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    })
  }),
)
