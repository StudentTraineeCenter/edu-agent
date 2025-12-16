import { Atom } from '@effect-atom/atom-react'
import { Array as Arr, Data, Effect, Order } from 'effect'
import { flashcardGroupsAtom } from './flashcard'
import { mindMapsAtom } from './mind-map'
import { notesAtom } from './note'
import { quizzesAtom } from './quiz'
import type {
  FlashcardGroupDto,
  MindMapDto,
  NoteDto,
  QuizDto,
} from '@/integrations/api/client'

export type StudyResource = Data.TaggedEnum<{
  FlashcardGroup: { readonly data: FlashcardGroupDto }
  Quiz: { readonly data: QuizDto }
  Note: { readonly data: NoteDto }
  MindMap: { readonly data: MindMapDto }
}>
export const StudyResource = Data.taggedEnum<StudyResource>()

export const studyResourcesAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.fn(function* (ctx) {
      const flashcardGroupsResult = ctx
        .result(flashcardGroupsAtom(projectId))
        .pipe(
          Effect.map((val) =>
            val.map((item) => StudyResource.FlashcardGroup({ data: item })),
          ),
        )

      const quizzesResult = ctx
        .result(quizzesAtom(projectId))
        .pipe(
          Effect.map((val) =>
            val.map((item) => StudyResource.Quiz({ data: item })),
          ),
        )

      const notesResult = ctx
        .result(notesAtom(projectId))
        .pipe(
          Effect.map((val) =>
            val.map((item) => StudyResource.Note({ data: item })),
          ),
        )

      const mindMapsResult = ctx
        .result(mindMapsAtom(projectId))
        .pipe(
          Effect.map((mindMaps) =>
            mindMaps.map((item) => StudyResource.MindMap({ data: item })),
          ),
        )

      const byCreatedAt = Order.mapInput(
        Order.Date,
        (resource: StudyResource) =>
          new Date(
            'generated_at' in resource.data
              ? resource.data.generated_at
              : resource.data.created_at,
          ),
      )

      return yield* Effect.all(
        [flashcardGroupsResult, quizzesResult, notesResult, mindMapsResult],
        { concurrency: 'unbounded' },
      ).pipe(
        Effect.flatMap(([flashcardGroups, quizzes, notes, mindMaps]) => {
          return Effect.succeed([
            ...flashcardGroups,
            ...quizzes,
            ...notes,
            ...mindMaps,
          ])
        }),
        Effect.map(Arr.sort(byCreatedAt)),
      )
    }),
  ).pipe(Atom.keepAlive),
)
