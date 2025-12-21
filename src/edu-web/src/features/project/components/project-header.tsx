import { useConfirmationDialog } from '@/components/confirmation-dialog'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Button, buttonVariants } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Skeleton } from '@/components/ui/skeleton'
import { deleteProjectAtom, projectAtom } from '@/data-acess/project'
import { cn } from '@/lib/utils'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { Link, useNavigate } from '@tanstack/react-router'
import { PencilIcon, TrashIcon } from 'lucide-react'
import { useCreateProjectDialog } from './upsert-project-dialog'

const ProjectHeaderContent = ({ projectId }: { projectId: string }) => {
  const projectResult = useAtomValue(projectAtom(projectId))

  return Result.builder(projectResult)
    .onSuccess((project) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {project.name}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .render()
}

type ProjectHeaderProps = {
  projectId: string
}

export const ProjectHeader = ({ projectId }: ProjectHeaderProps) => {
  const projectResult = useAtomValue(projectAtom(projectId))
  const deleteProject = useAtomSet(deleteProjectAtom, { mode: 'promise' })
  const navigate = useNavigate()
  const confirmationDialog = useConfirmationDialog()
  const openEditDialog = useCreateProjectDialog((state) => state.open)

  const handleEdit = () => {
    if (Result.isSuccess(projectResult)) {
      openEditDialog(projectResult.value)
    }
  }

  const handleDelete = async () => {
    const confirmed = await confirmationDialog.open({
      title: 'Delete Project',
      description:
        'Are you sure you want to delete this project? This action cannot be undone and will delete all associated chats, documents, and AI content.',
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    })

    if (confirmed) {
      await deleteProject(projectId)
      navigate({ to: '/' })
    }
  }

  return (
    <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(projectResult) && <SidebarTrigger />}
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <ProjectHeaderContent projectId={projectId} />
      </div>
      {Result.isSuccess(projectResult) && (
        <div className="flex items-center gap-2 px-3">
          <Link
            to="/dashboard/p/$projectId/study-plan"
            params={{
              projectId,
            }}
            className={cn(buttonVariants({ variant: 'ghost' }))}
          >
            Study Plan
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={handleEdit}
          >
            <PencilIcon className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={handleDelete}
          >
            <TrashIcon className="size-4" />
          </Button>
        </div>
      )}
    </header>
  )
}
