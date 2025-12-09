import { Atom, Registry } from '@effect-atom/atom-react'
import { makeApiClient, makeHttpClient } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { HttpBody } from '@effect/platform'
import { runtime } from './runtime'

export const mindMapsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const apiClient = yield* makeApiClient
      const mindMaps =
        yield* apiClient.listMindMapsV1ProjectsProjectIdMindMapsGet(projectId)
      return mindMaps
    }),
  ).pipe(Atom.keepAlive),
)

export const mindMapAtom = Atom.family((mindMapId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const apiClient = yield* makeApiClient
      const mindMap = yield* apiClient
        .getMindMapV1MindMapsMindMapIdGet(mindMapId)
        .pipe(
          Effect.catchTag('ResponseError', (error) => {
            if (error.response.status === 404) {
              return Effect.succeed(null)
            }
            return Effect.fail(error)
          }),
        )

      return mindMap
    }),
  ).pipe(Atom.keepAlive),
)

const MindMapProgressUpdate = Schema.Struct({
  status: Schema.String,
  message: Schema.String,
  mind_map_id: Schema.NullishOr(Schema.String),
  error: Schema.NullishOr(Schema.String),
})

export const mindMapProgressAtom = Atom.make<{
  status: string
  message: string
  error?: string
} | null>(null)

export const generateMindMapStreamAtom = Atom.fn(
  Effect.fn(function* (
    input: { projectId: string; customInstructions?: string },
    _get: Atom.FnContext,
  ) {
    const httpClient = yield* makeHttpClient
    const body = HttpBody.unsafeJson({
      custom_instructions: input.customInstructions || null,
    })
    const resp = yield* httpClient.post(
      `/v1/projects/${input.projectId}/mind-maps/stream`,
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
            Schema.decodeUnknown(Schema.parseJson(MindMapProgressUpdate))(line),
          ),
        )
      }),
      Stream.tap((progress) =>
        Effect.gen(function* () {
          const registry = yield* Registry.AtomRegistry
          registry.set(mindMapProgressAtom, {
            status: progress.status,
            message: progress.message,
            error: progress.error ?? undefined,
          })
        }),
      ),
    )

    yield* Stream.runCollect(respStream)

    // Refresh mind maps list after completion
    const registry = yield* Registry.AtomRegistry
    if (input.projectId) {
      registry.refresh(mindMapsAtom(input.projectId))
    }
    registry.set(mindMapProgressAtom, null)
  }),
).pipe(Atom.keepAlive)

export const generateMindMapAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    customInstructions?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const apiClient = yield* makeApiClient
    const mindMap =
      yield* apiClient.generateMindMapV1ProjectsProjectIdMindMapsPost(
        input.projectId,
        {
          custom_instructions: input.customInstructions,
        },
      )
    // Refresh both the list and the individual mind map atom
    registry.refresh(mindMapsAtom(input.projectId))
    registry.refresh(mindMapAtom(mindMap.id))
    return mindMap
  }),
)
