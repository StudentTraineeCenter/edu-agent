import { makeApiClient } from '@/integrations/api/http'
import { Effect } from 'effect'
import { Atom, Registry } from '@effect-atom/atom-react'
import { runtime } from './runtime'
import { CreateQuizRequest } from '@/integrations/api/client'

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
      return resp.data
    }),
  ).pipe(Atom.keepAlive),
)

export const createQuizAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    questionCount?: number
    userPrompt?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createQuizV1QuizzesPost({
      params: { project_id: input.projectId },
      payload: new CreateQuizRequest({
        question_count: input.questionCount,
        user_prompt: input.userPrompt,
      }),
    })

    registry.refresh(quizzesAtom(input.projectId))
    return resp.quiz
  }),
)

export const deleteQuizAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; projectId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteQuizV1QuizzesQuizIdDelete(input.quizId)

    registry.refresh(quizzesAtom(input.projectId))
  }),
)
