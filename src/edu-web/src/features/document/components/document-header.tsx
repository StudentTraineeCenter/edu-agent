import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Skeleton } from '@/components/ui/skeleton'
import { documentAtom } from '@/data-acess/document'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Link } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'

const DocumentHeaderContent = ({
  projectId,
  documentId,
}: {
  projectId: string
  documentId: string
}) => {
  const documentResult = useAtomValue(
    documentAtom(`${projectId}:${documentId}`),
  )

  return Result.builder(documentResult)
    .onSuccess((document) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {document.file_name ?? 'Untitled document'}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .render()
}

type DocumentHeaderProps = {
  documentId: string
  projectId: string
}

export const DocumentHeader = ({
  documentId,
  projectId,
}: DocumentHeaderProps) => {
  const documentResult = useAtomValue(
    documentAtom(`${projectId}:${documentId}`),
  )

  return (
    <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(documentResult) && (
          <>
            <SidebarTrigger />
            <Button variant="ghost" size="icon" className="size-7" asChild>
              <Link to="/dashboard/p/$projectId" params={{ projectId }}>
                <ArrowLeft className="size-4" />
                <span className="sr-only">Back to project</span>
              </Link>
            </Button>
          </>
        )}
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <DocumentHeaderContent projectId={projectId} documentId={documentId} />
      </div>
    </header>
  )
}
