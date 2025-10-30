import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { Data, Effect, Array } from 'effect'

import { makeApiClient } from '@/integrations/api/http'
import {
  ProjectDto,
  type ProjectCreateRequest,
} from '@/integrations/api/client'
import { runtime } from '@/data-acess/runtime'

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
    const resp = yield* client.listProjectsV1ProjectsGet()
    return resp.data
  }),
)

export const projectAtom = Atom.family((projectId: string) =>
  Atom.make(
    Effect.gen(function* () {
      const client = yield* makeApiClient
      return yield* client.getProjectV1ProjectsProjectIdGet(projectId)
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
  Effect.fn(function* (input: typeof ProjectCreateRequest.Encoded) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    const res = yield* client.createProjectV1ProjectsPost(input)

    registry.set(projectsAtom, ProjectsAction.Upsert({ project: res }))
    registry.refresh(projectsRemoteAtom)
  }),
)

export const deleteProjectAtom = runtime.fn(
  Effect.fn(function* (projectId: string) {
    const registry = yield* Registry.AtomRegistry
    const client = yield* makeApiClient
    yield* client.archiveProjectV1ProjectsProjectIdArchivePost(projectId)

    registry.set(projectsAtom, ProjectsAction.Del({ projectId }))
    registry.refresh(projectsRemoteAtom)
  }),
)
