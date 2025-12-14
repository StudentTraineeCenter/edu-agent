import { Atom, Registry } from '@effect-atom/atom-react'
import { ApiClientService } from '@/integrations/api/http'
import { Effect, Schema, Stream } from 'effect'
import { HttpBody } from '@effect/platform'
import { MindMapCreate } from '@/integrations/api/client'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Layer } from 'effect'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    ApiClientService.Default,
  ),
)

export const mindMapsAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      const mindMaps =
        yield* apiClient.listMindMapsApiV1ProjectsProjectIdMindMapsGet(
          projectId,
        )
      return mindMaps
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive),
)

export const mindMapAtom = Atom.family((key: string) => {
  const [projectId, mindMapId] = key.split(':')
  return Atom.make(
    Effect.gen(function* () {
      const { apiClient } = yield* ApiClientService
      const mindMap =
        yield* apiClient.getMindMapApiV1ProjectsProjectIdMindMapsMindMapIdGet(
          projectId,
          mindMapId,
        )
      return mindMap
    }).pipe(Effect.provide(ApiClientService.Default)),
  ).pipe(Atom.keepAlive)
})

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
  (
    input: {
      projectId: string
      customInstructions?: string
    },
    _get,
  ) =>
    Effect.gen(function* () {
      const { httpClient } = yield* ApiClientService
      const body = HttpBody.unsafeJson({
        custom_instructions: input.customInstructions || null,
      })
      const resp = yield* httpClient.post(
        `/api/v1/projects/${input.projectId}/mind-maps/stream`,
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
              Schema.decodeUnknown(Schema.parseJson(MindMapProgressUpdate))(
                line,
              ),
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
    }).pipe(Effect.provide(ApiClientService.Default)),
).pipe(Atom.keepAlive)

export const generateMindMapAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    title?: string
    description?: string
    customInstructions?: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const mindMap =
      yield* apiClient.createMindMapApiV1ProjectsProjectIdMindMapsPost(
        input.projectId,
        new MindMapCreate({
          title: input.title ?? 'New Mind Map',
          description: input.description,
          custom_instructions: input.customInstructions,
        }),
      )

    // Refresh both the list and the individual mind map atom
    registry.refresh(mindMapsAtom(input.projectId))
    registry.refresh(mindMapAtom(`${input.projectId}:${mindMap.id}`))
    return mindMap
  }),
)
