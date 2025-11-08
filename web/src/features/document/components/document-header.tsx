import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue } from '@effect-atom/atom-react'
import { documentAtom } from '@/data-acess/document'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'

const DocumentHeaderContent = ({ documentId }: { documentId: string }) => {
  const documentResult = useAtomValue(documentAtom(documentId))

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
}

export const DocumentHeader = ({ documentId }: DocumentHeaderProps) => {
  const documentResult = useAtomValue(documentAtom(documentId))

  return (
    <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(documentResult) && <SidebarTrigger />}
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <DocumentHeaderContent documentId={documentId} />
      </div>
    </header>
  )
}
