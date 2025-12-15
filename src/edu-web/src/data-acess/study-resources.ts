import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Effect, Order, Array as Arr, Data } from 'effect'
import { flashcardGroupsAtom } from './flashcard'
import { notesAtom } from './note'
import { quizzesAtom } from './quiz'
import { mindMapsAtom } from './mind-map'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { ApiClientService } from '@/integrations/api/http'
import { Layer } from 'effect'
import type {
  FlashcardGroupDto,
  NoteDto,
  QuizDto,
  MindMapDto,
} from '@/integrations/api/client'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

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
