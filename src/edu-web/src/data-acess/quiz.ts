import { ApiClientService } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { Atom, Registry } from '@effect-atom/atom-react'
import { HttpBody } from '@effect/platform'
import {
  QuizCreate,
  GenerateRequest,
  QuizQuestionCreate,
  QuizQuestionUpdate,
  QuizQuestionReorder,
} from '@/integrations/api/client'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { withToast } from '@/lib/with-toast'
import { Layer } from 'effect'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

export const quizzesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      return yield* apiClient.listQuizzesApiV1ProjectsProjectIdQuizzesGet(
        projectId,
      )
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive),
)

export const quizAtom = Atom.family(
  (input: { projectId: string; quizId: string }) =>
    Atom.make(
      Effect.gen(function* () {
        const { apiClient } = yield* ApiClientService
        return yield* apiClient.getQuizApiV1ProjectsProjectIdQuizzesQuizIdGet(
          input.projectId,
          input.quizId,
        )
      }).pipe(Effect.provide(ApiClientService.Default)),
    ).pipe(Atom.keepAlive),
)

export const quizQuestionsAtom = Atom.family(
  (input: { projectId: string; quizId: string }) =>
    Atom.make(
      Effect.gen(function* () {
        const { apiClient } = yield* ApiClientService
        return yield* apiClient.listQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsGet(
          input.projectId,
          input.quizId,
        )
      }).pipe(Effect.provide(ApiClientService.Default)),
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
  (
    input: {
      projectId: string
      quizId: string
      questionCount: number
      customInstructions?: string
      topic?: string
      difficulty?: string
    },
    _get,
  ) =>
    Effect.gen(function* () {
      const registry = yield* Registry.AtomRegistry
      const { httpClient } = yield* ApiClientService
      const body = HttpBody.unsafeJson(
        new GenerateRequest({
          count: input.questionCount,
          custom_instructions: input.customInstructions,
          topic: input.topic,
          difficulty: input.difficulty,
        }),
      )
      const resp = yield* httpClient.post(
        `/api/v1/projects/${input.projectId}/quizzes/${input.quizId}/generate/stream`,
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
    }).pipe(Effect.provide(ApiClientService.Default)),
).pipe(Atom.keepAlive)

export const createQuizAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    name?: string
    description?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp = yield* apiClient.createQuizApiV1ProjectsProjectIdQuizzesPost(
      input.projectId,
      new QuizCreate({
        name: input.name ?? 'New Quiz',
        description: input.description,
      }),
    )

    registry.refresh(quizzesAtom(input.projectId))
    return resp
  }),
)

export const deleteQuizAtom = runtime.fn(
  Effect.fn(
    function* (input: { quizId: string; projectId: string }) {
      const registry = yield* Registry.AtomRegistry
      const { apiClient } = yield* ApiClientService
      yield* apiClient.deleteQuizApiV1ProjectsProjectIdQuizzesQuizIdDelete(
        input.projectId,
        input.quizId,
      )

      registry.refresh(quizzesAtom(input.projectId))
    },
    withToast({
      onWaiting: () => 'Deleting quiz...',
      onSuccess: 'Quiz deleted',
      onFailure: 'Failed to delete quiz',
    }),
  ),
)

export const exportQuizAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; quizId: string }) {
    yield* Effect.log(
      `Exporting quiz ${input.quizId} for project ${input.projectId}`,
    )
    // Note: Quiz export endpoints may not be available in the new API
    // This might need to be handled differently or removed if not supported
    // For now, commenting out as the endpoint doesn't exist in the client
    // const client = yield* makeApiClient
    // const response = yield* client.exportQuiz(...)
    throw new Error('Quiz export not supported in current API')
  }),
)

export const importQuizAtom = runtime.fn(
  Effect.fn(function* (input: { projectId: string; file: File }) {
    const registry = yield* Registry.AtomRegistry
    // Note: Quiz import endpoints may not be available in the new API
    // This might need to be handled differently or removed if not supported
    // For now, commenting out as the endpoint doesn't exist in the client
    // const client = yield* makeApiClient
    // const response = yield* client.importQuiz(...)

    registry.refresh(quizzesAtom(input.projectId))
    throw new Error('Quiz import not supported in current API')
  }),
)

export const createQuizQuestionAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
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
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.createQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsPost(
        input.projectId,
        input.quizId,
        new QuizQuestionCreate({
          question_text: input.questionText,
          option_a: input.optionA,
          option_b: input.optionB,
          option_c: input.optionC,
          option_d: input.optionD,
          correct_option: input.correctOption,
          explanation: input.explanation,
          difficulty_level: input.difficultyLevel || 'medium',
          position: input.position,
        }),
      )

    registry.refresh(
      quizQuestionsAtom({ projectId: input.projectId, quizId: input.quizId }),
    )
    return resp
  }),
)

export const updateQuizQuestionAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
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
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.updateQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdPatch(
        input.projectId,
        input.quizId,
        input.questionId,
        new QuizQuestionUpdate({
          question_text: input.questionText,
          option_a: input.optionA,
          option_b: input.optionB,
          option_c: input.optionC,
          option_d: input.optionD,
          correct_option: input.correctOption,
          explanation: input.explanation,
          difficulty_level: input.difficultyLevel,
        }),
      )

    registry.refresh(
      quizQuestionsAtom({ projectId: input.projectId, quizId: input.quizId }),
    )
    return resp
  }),
)

export const deleteQuizQuestionAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    quizId: string
    questionId: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    yield* apiClient.deleteQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdDelete(
      input.projectId,
      input.quizId,
      input.questionId,
    )

    registry.refresh(
      quizQuestionsAtom({ projectId: input.projectId, quizId: input.quizId }),
    )
  }),
)

export const reorderQuizQuestionsAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    quizId: string
    questionIds: string[]
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const resp =
      yield* apiClient.reorderQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsReorderPatch(
        input.projectId,
        input.quizId,
        new QuizQuestionReorder({
          question_ids: input.questionIds,
        }),
      )

    registry.refresh(
      quizQuestionsAtom({ projectId: input.projectId, quizId: input.quizId }),
    )
    return resp
  }),
)
