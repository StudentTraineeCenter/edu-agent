import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useProjectsQuery } from '@/data-acess/project'
import type { Project } from '@/integrations/api'
import { useNavigate } from '@tanstack/react-router'
import { ArrowRightIcon, PlusIcon } from 'lucide-react'
import { useCreateProjectDialog } from '@/components/projects/create-project-dialog'

const ProjectsHeader = ({ onCreate }: { onCreate: () => void }) => (
  <div className="mb-8 flex items-center justify-between">
    <div>
      <h1 className="text-4xl font-bold tracking-tight mb-4">Projects</h1>
      <p className="text-xl text-muted-foreground">
        Select a project to continue learning
      </p>
    </div>
    <Button onClick={onCreate} className="gap-2">
      <PlusIcon className="w-4 h-4" />
      Add Project
    </Button>
  </div>
)

const ProjectsEmptyRow = () => (
  <TableRow>
    <TableCell colSpan={2} className="text-center text-muted-foreground py-8">
      No projects found. Create your first project to get started.
    </TableCell>
  </TableRow>
)

const ProjectRow = ({
  project,
  onOpen,
}: {
  project: Project
  onOpen: (p: Project) => void
}) => (
  <TableRow key={project.id}>
    <TableCell className="font-medium">{project.name}</TableCell>
    <TableCell>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onOpen(project)}
        className="gap-2"
      >
        Open
        <ArrowRightIcon className="w-4 h-4" />
      </Button>
    </TableCell>
  </TableRow>
)

const ProjectsTable = ({
  projects,
  onOpen,
}: {
  projects: Project[]
  onOpen: (p: Project) => void
}) => (
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
          <ProjectRow key={project.id} project={project} onOpen={onOpen} />
        ))}
        {projects.length === 0 && <ProjectsEmptyRow />}
      </TableBody>
    </Table>
  </div>
)

export const ProjectListPage = () => {
  const projectsQuery = useProjectsQuery()
  const projects = projectsQuery.data?.data ?? []

  const navigate = useNavigate()
  const { open: openCreateProjectDialog } = useCreateProjectDialog()

  const handleCreateProject = () => {
    openCreateProjectDialog()
  }

  const handleProjectClick = async (project: Project) => {
    await navigate({
      to: '/projects/$projectId',
      params: {
        projectId: project.id,
      },
    })
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto py-12 max-w-5xl">
        <ProjectsHeader onCreate={handleCreateProject} />
        <ProjectsTable projects={projects} onOpen={handleProjectClick} />
      </main>
    </div>
  )
}
