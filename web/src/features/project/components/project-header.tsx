import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue } from '@effect-atom/atom-react'
import { projectAtom } from '@/data-acess/project'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'

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
    </header>
  )
}
