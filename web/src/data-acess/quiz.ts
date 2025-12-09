import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { Atom, Registry } from '@effect-atom/atom-react'
import { HttpBody } from '@effect/platform'
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

const QuizProgressUpdate = Schema.Struct({
  status: Schema.String,
  message: Schema.String,
  quiz_id: Schema.NullishOr(Schema.String),
  error: Schema.NullishOr(Schema.String),
})

export const quizProgressAtom = Atom.make<{
  status: string
  message: string
  error?: string
} | null>(null)

export const createQuizStreamAtom = Atom.fn(
  Effect.fn(function* (
    input: {
      projectId: string
      questionCount?: number
      customInstructions?: string
      length?: string
      difficulty?: string
    },
    _get: Atom.FnContext,
  ) {
    const registry = yield* Registry.AtomRegistry
    const httpClient = yield* makeHttpClient
    const body = HttpBody.unsafeJson(
      new CreateQuizRequest({
        question_count: input.questionCount,
        custom_instructions: input.customInstructions,
        length: input.length,
        difficulty: input.difficulty,
      }),
    )
    const resp = yield* httpClient.post(
      `/v1/quizzes/stream?project_id=${input.projectId}`,
      { body },
    )

    const decoder = new TextDecoder()
    const respStream = resp.stream.pipe(
      Stream.map((value) => decoder.decode(value, { stream: true })),
      Stream.map((chunk) => {
        const chunkLines = chunk.split('\n')
        const res = chunkLines
          .map((line) =>
            line.startsWith('data: ') ? line.replace('data: ', '') : '',
          )
          .filter((line) => line !== '')
          .join('\n')
        return res
      }),
      Stream.filter((chunk) => chunk !== ''),
      Stream.flatMap((chunk) => {
        const lines = chunk.trim().split('\n')
        return Stream.fromIterable(lines).pipe(
          Stream.filter((line) => line.trim() !== ''),
          Stream.flatMap((line) =>
            Schema.decodeUnknown(Schema.parseJson(QuizProgressUpdate))(line),
          ),
        )
      }),
      Stream.tap((progress) =>
        Effect.sync(() => {
          registry.set(quizProgressAtom, {
            status: progress.status,
            message: progress.message,
            error: progress.error ?? undefined,
          })
        }),
      ),
    )

    yield* Stream.runCollect(respStream)

    // Refresh quizzes list after completion
    if (input.projectId) {
      registry.refresh(quizzesAtom(input.projectId))
    }

    // Clear progress when done
    registry.set(quizProgressAtom, null)
  }),
).pipe(Atom.keepAlive)

export const createQuizAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    questionCount?: number
    customInstructions?: string
    length?: string
    difficulty?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createQuizV1QuizzesPost({
      params: { project_id: input.projectId },
      payload: new CreateQuizRequest({
        question_count: input.questionCount,
        custom_instructions: input.customInstructions,
        length: input.length,
        difficulty: input.difficulty,
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

export const exportQuizAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string }) {
    const client = yield* makeApiClient
    const response = yield* client.exportQuizV1QuizzesQuizIdExportGet(
      input.quizId,
    )
    return response
  }),
)

export const importQuizAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; file: File }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient

    const response =
      yield* client.importQuizV1ProjectsProjectIdQuizzesImportPost(
        input.projectId,
        {
          file: input.file,
          quiz_name: '',
          quiz_description: '',
        },
      )

    registry.refresh(quizzesAtom(input.projectId))
    return response
  }),
)

export const createQuizQuestionAtom = runtime.fn(
  Effect.fn(function* (input: {
    quizId: string
    questionText: string
    optionA: string
    optionB: string
    optionC: string
    optionD: string
    correctOption: string
    explanation?: string
    difficultyLevel?: string
    position?: number
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp = yield* client.createQuizQuestionV1QuizzesQuizIdQuestionsPost(
      input.quizId,
      {
        question_text: input.questionText,
        option_a: input.optionA,
        option_b: input.optionB,
        option_c: input.optionC,
        option_d: input.optionD,
        correct_option: input.correctOption,
        explanation: input.explanation,
        difficulty_level: input.difficultyLevel || 'medium',
        position: input.position,
      },
    )

    registry.refresh(quizQuestionsAtom(input.quizId))
    return resp.question
  }),
)

export const updateQuizQuestionAtom = runtime.fn(
  Effect.fn(function* (input: {
    quizId: string
    questionId: string
    questionText?: string
    optionA?: string
    optionB?: string
    optionC?: string
    optionD?: string
    correctOption?: string
    explanation?: string
    difficultyLevel?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp =
      yield* client.updateQuizQuestionV1QuizzesQuizIdQuestionsQuestionIdPatch(
        input.quizId,
        input.questionId,
        {
          question_text: input.questionText,
          option_a: input.optionA,
          option_b: input.optionB,
          option_c: input.optionC,
          option_d: input.optionD,
          correct_option: input.correctOption,
          explanation: input.explanation,
          difficulty_level: input.difficultyLevel,
        },
      )

    registry.refresh(quizQuestionsAtom(input.quizId))
    return resp.question
  }),
)

export const deleteQuizQuestionAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; questionId: string }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.deleteQuizQuestionV1QuizzesQuizIdQuestionsQuestionIdDelete(
      input.quizId,
      input.questionId,
    )

    registry.refresh(quizQuestionsAtom(input.quizId))
  }),
)

export const reorderQuizQuestionsAtom = runtime.fn(
  Effect.fn(function* (input: { quizId: string; questionIds: string[] }) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const resp =
      yield* client.reorderQuizQuestionsV1QuizzesQuizIdQuestionsReorderPatch(
        input.quizId,
        {
          question_ids: input.questionIds,
        },
      )

    registry.refresh(quizQuestionsAtom(input.quizId))
    return resp.data
  }),
)
