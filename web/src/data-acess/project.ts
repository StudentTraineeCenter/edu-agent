import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Array } from 'effect'
import { makeApiClient } from '@/integrations/api/http'
import {
  ProjectDto,
  ProjectCreate,
  ProjectUpdate,
} from '@/integrations/api/client'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { withToast } from '@/lib/with-toast'

const runtime = makeAtomRuntime(BrowserKeyValueStore.layerLocalStorage)

export const currentProjectIdAtom = Atom.make<string | null>(null).pipe(
  Atom.keepAlive,
)

type ProjectsAction = Data.TaggedEnum<{
  Upsert: { readonly project: ProjectDto }
  Del: { readonly projectId: string }
}>
const ProjectsAction = Data.taggedEnum<ProjectsAction>()

export const projectsRemoteAtom = runtime.atom(
  Effect.fn(function* () {
    const client = yield* makeApiClient
    const resp = yield* client.listProjectsApiV1ProjectsGet()
    return resp
  }),
)

export const projectAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.getProjectApiV1ProjectsProjectIdGet(projectId)
    }),
  ).pipe(Atom.keepAlive),
)

export const projectsAtom = Object.assign(
  Atom.writable(
    (get: Atom.Context) => get(projectsRemoteAtom),
    (ctx, action: ProjectsAction) => {
      const result = ctx.get(projectsAtom)
      if (!Result.isSuccess(result)) return

      const update = ProjectsAction.$match(action, {
        Upsert: ({ project }) => {
          const existing = result.value.find((p) => p.id === project.id)
          if (existing)
            return result.value.map((p) => (p.id === project.id ? project : p))
          return Array.prepend(result.value, project)
        },
        Del: ({ projectId }) => {
          return result.value.filter((p) => p.id !== projectId)
        },
      })

      ctx.setSelf(Result.success(update))
    },
  ),
  {
    remote: projectsRemoteAtom,
  },
)

export const upsertProjectAtom = runtime.fn(
  Effect.fn(
    function* (input: typeof ProjectCreate.Encoded & { id?: string }) {
      const registry = yield* Registry.AtomRegistry
      const client = yield* makeApiClient
      const { id, ...data } = input

      const res = id
        ? yield* client.updateProjectApiV1ProjectsProjectIdPatch(
            id,
            data as typeof ProjectUpdate.Encoded,
          )
        : yield* client.createProjectApiV1ProjectsPost(
            data as typeof ProjectCreate.Encoded,
          )

      registry.set(projectsAtom, ProjectsAction.Upsert({ project: res }))
      registry.refresh(projectsRemoteAtom)
      if (id) {
        registry.refresh(projectAtom(id))
      }
    },
    withToast({
      onWaiting: () => 'Creating project...',
      onSuccess: 'Project created',
      onFailure: 'Failed to create project',
    }),
  ),
)

export const deleteProjectAtom = runtime.fn(
  Effect.fn(
    function* (projectId: string) {
      const registry = yield* Registry.AtomRegistry
      const client = yield* makeApiClient
      yield* client.deleteProjectApiV1ProjectsProjectIdDelete(projectId)

      registry.set(projectsAtom, ProjectsAction.Del({ projectId }))
      registry.refresh(projectsRemoteAtom)
    },
    withToast({
      onWaiting: () => 'Deleting project...',
      onSuccess: 'Project deleted',
      onFailure: 'Failed to delete project',
    }),
  ),
)
