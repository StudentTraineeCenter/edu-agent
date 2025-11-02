import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { projectsAtom } from '@/data-acess/project'
import { useNavigate } from '@tanstack/react-router'
import { ArrowRightIcon, PlusIcon } from 'lucide-react'
import { useCreateProjectDialog } from '@/components/projects/upsert-project-dialog'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import type { ProjectDto } from '@/integrations/api/client'
import { Cause } from 'effect'

const ProjectsHeader = () => {
  const openDialog = useCreateProjectDialog().open

  return (
    <div className="mb-8 flex items-center justify-between">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Projects</h1>
        <p className="text-xl text-muted-foreground">
          Select a project to continue learning
        </p>
      </div>
      <Button onClick={() => openDialog()} className="gap-2">
        <PlusIcon className="size-4" />
        Add Project
      </Button>
    </div>
  )
}

const ProjectsEmptyRow = () => (
  <TableRow>
    <TableCell colSpan={2} className="text-center text-muted-foreground py-8">
      No projects found. Create your first project to get started.
    </TableCell>
  </TableRow>
)

const ProjectRow = ({ project }: { project: ProjectDto }) => {
  const navigate = useNavigate()

  const handleProjectClick = async () => {
    await navigate({
      to: '/projects/$projectId',
      params: {
        projectId: project.id,
      },
    })
  }

  return (
    <TableRow key={project.id}>
      <TableCell className="font-medium">{project.name}</TableCell>
      <TableCell>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleProjectClick}
          className="gap-2"
        >
          Open
          <ArrowRightIcon className="size-4" />
        </Button>
      </TableCell>
    </TableRow>
  )
}

const ProjectsTable = ({
  projects,
}: {
  projects: ReadonlyArray<ProjectDto>
}) => {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {projects.map((project) => (
            <ProjectRow key={project.id} project={project} />
          ))}
          {projects.length === 0 && <ProjectsEmptyRow />}
        </TableBody>
      </Table>
    </div>
  )
}

export const ProjectListPage = () => {
  const projectsResult = useAtomValue(projectsAtom)

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto py-12 max-w-5xl">
        <ProjectsHeader />

        {Result.builder(projectsResult)
          .onInitialOrWaiting(() => <div>Loading...</div>)
          .onFailure((cause) => <div>Error: {Cause.pretty(cause)}</div>)
          .onSuccess((projects) => <ProjectsTable projects={projects} />)
          .render()}
      </main>
    </div>
  )
}
