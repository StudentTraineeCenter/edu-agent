import { Atom, Result } from '@effect-atom/atom-react'
import { Effect, Order, Array as Arr, Data } from 'effect'
import { flashcardGroupsAtom } from './flashcard'
import { quizzesAtom } from './quiz'
import type { FlashcardGroupDto, QuizDto } from '@/integrations/api/client'

export type StudyResource = Data.TaggedEnum<{
  FlashcardGroup: { readonly data: FlashcardGroupDto }
  Quiz: { readonly data: QuizDto }
}>
export const StudyResource = Data.taggedEnum<StudyResource>()

export const studyResourcesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.fn(function* (ctx) {
      const flashcardGroupsResult = ctx
        .get(flashcardGroupsAtom(projectId))
        .pipe(
          Result.map((val) =>
            val.data.map((item) =>
              StudyResource.FlashcardGroup({ data: item }),
            ),
          ),
        )

      const quizzesResult = ctx
        .get(quizzesAtom(projectId))
        .pipe(
          Result.map((val) =>
            val.data.map((item) => StudyResource.Quiz({ data: item })),
          ),
        )

      const byCreatedAt = Order.mapInput(
        Order.Date,
        (resource: StudyResource) => new Date(resource.data.created_at),
      )

      return Result.all([flashcardGroupsResult, quizzesResult]).pipe(
        Result.map(([flashcardGroups, quizzes]) => {
          return [...flashcardGroups, ...quizzes]
        }),
        Result.map(Arr.sort(byCreatedAt)),
        Result.getOrElse(() => []),
      )
    }),
  ).pipe(Atom.keepAlive),
)
