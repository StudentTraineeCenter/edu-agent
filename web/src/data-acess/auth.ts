import { Atom } from '@effect-atom/atom-react'
import { Effect } from 'effect'
import { makeApiClient } from '@/integrations/api/http'

export const ME_QUERY_KEY = () => ['me']

export const meAtom = Atom.make(
  Effect.gen(function* () {
    const client = yield* makeApiClient
    return yield* client.getCurrentUserInfoV1AuthMeGet()
  }),
).pipe(Atom.keepAlive)

// Profile photo is now handled via Supabase user_metadata.avatar_url
// This atom is kept for compatibility but returns null
export const profilePhotoAtom = Atom.make(
  Effect.succeed(null as string | null),
).pipe(Atom.keepAlive)
