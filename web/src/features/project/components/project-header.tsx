import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { projectAtom, deleteProjectAtom } from '@/data-acess/project'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { TrashIcon, PencilIcon } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { useConfirmationDialog } from '@/components/confirmation-dialog'
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
        'Are you sure you want to delete this project? This action cannot be undone and will delete all associated chats, documents, and study resources.',
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
