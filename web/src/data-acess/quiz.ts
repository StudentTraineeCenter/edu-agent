import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { Atom, Registry } from '@effect-atom/atom-react'
import { runtime } from './runtime'

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
      const resp =
        yield* client.listQuizQuestionsV1QuizzesQuizIdQuestionsGet(quizId)
      return resp.quiz_questions
    }),
  ).pipe(Atom.keepAlive),
)

export const deleteQuizAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteQuizV1QuizzesQuizIdDelete(input.quizId)

    registry.refresh(quizzesAtom(input.projectId))
  }),
)
