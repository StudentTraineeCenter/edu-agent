import { useAtomValue } from '@effect-atom/atom-react'
import { Result } from '@effect-atom/atom-react'
import { projectsAtom } from '@/data-acess/project'
import { Link } from '@tanstack/react-router'
import { FolderIcon, PlusIcon } from 'lucide-react'
import { useCreateProjectDialog } from '@/features/project/components/upsert-project-dialog'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const DashboardPage = () => {
  const projectsResult = useAtomValue(projectsAtom)
  const openCreateProjectDialog = useCreateProjectDialog((state) => state.open)

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground mt-2">
              Manage your projects and organize your learning materials
            </p>
          </div>
          <Button onClick={() => openCreateProjectDialog()}>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>

        {Result.builder(projectsResult)
          .onInitialOrWaiting(() => (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading projects...</p>
            </div>
          ))
          .onFailure(() => (
            <div className="text-center py-12">
              <p className="text-destructive">Failed to load projects</p>
            </div>
          ))
          .onSuccess((projects) => {
            if (projects.length === 0) {
              return (
                <Card>
                  <CardHeader>
                    <CardTitle>No projects yet</CardTitle>
                    <CardDescription>
                      Get started by creating your first project
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button onClick={() => openCreateProjectDialog()}>
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Create Project
                    </Button>
                  </CardContent>
                </Card>
              )
            }

            return (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <Card
                    key={project.id}
                    className="hover:shadow-md transition-shadow"
                  >
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FolderIcon className="h-5 w-5" />
                        <Link
                          to="/dashboard/p/$projectId"
                          params={{ projectId: project.id }}
                          className="hover:underline"
                        >
                          {project.name}
                        </Link>
                      </CardTitle>
                      {project.description && (
                        <CardDescription>{project.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <Link
                        to="/dashboard/p/$projectId"
                        params={{ projectId: project.id }}
                      >
                        <Button variant="outline" className="w-full">
                          Open Project
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )
          })
          .render()}
      </div>
    </div>
  )
}
