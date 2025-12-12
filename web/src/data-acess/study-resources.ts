import { Atom, Result } from '@effect-atom/atom-react'
import { Effect, Order, Array as Arr, Data } from 'effect'
import { flashcardGroupsAtom } from './flashcard'
import { notesAtom } from './note'
import { quizzesAtom } from './quiz'
import { mindMapsAtom } from './mind-map'
import type {
  FlashcardGroupDto,
  NoteDto,
  QuizDto,
  MindMapDto,
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
        .get(flashcardGroupsAtom(projectId))
        .pipe(
          Result.map((val) =>
            val.map((item) => StudyResource.FlashcardGroup({ data: item })),
          ),
        )

      const quizzesResult = ctx
        .get(quizzesAtom(projectId))
        .pipe(
          Result.map((val) =>
            val.map((item) => StudyResource.Quiz({ data: item })),
          ),
        )

      const notesResult = ctx
        .get(notesAtom(projectId))
        .pipe(
          Result.map((val) =>
            val.map((item) => StudyResource.Note({ data: item })),
          ),
        )

      const mindMapsResult = ctx
        .get(mindMapsAtom(projectId))
        .pipe(
          Result.map((mindMaps) =>
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

      return Result.all([
        flashcardGroupsResult,
        quizzesResult,
        notesResult,
        mindMapsResult,
      ]).pipe(
        Result.map(([flashcardGroups, quizzes, notes, mindMaps]) => {
          return [...flashcardGroups, ...quizzes, ...notes, ...mindMaps]
        }),
        Result.map(Arr.sort(byCreatedAt)),
        Result.getOrElse(() => []),
      )
    }),
  ).pipe(Atom.keepAlive),
)
