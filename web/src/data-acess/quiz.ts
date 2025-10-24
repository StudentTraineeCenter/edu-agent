import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { Atom } from '@effect-atom/atom-react'

export const quizzesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.listQuizzesV1QuizzesGet({
        project_id: projectId,
      })
    }),
  ).pipe(Atom.keepAlive),
)

export const quizAtom = Atom.family((quizId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.getQuizV1QuizzesQuizIdGet(quizId)
    }),
  ).pipe(Atom.keepAlive),
)

export const quizQuestionsAtom = Atom.family((quizId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.listQuizQuestionsV1QuizzesQuizIdQuestionsGet(quizId)
    }),
  ).pipe(Atom.keepAlive),
)
