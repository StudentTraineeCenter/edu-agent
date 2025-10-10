import {
  useDocumentPreviewQuery,
  useDocumentQuery,
} from '@/data-acess/document'
import { documentDetailRoute } from '@/routes/_config'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { FileIcon, Loader2Icon } from 'lucide-react'

const DocumentHeader = ({ title }: { title?: string }) => (
  <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2">
    <div className="flex flex-1 items-center gap-2 px-3">
      <SidebarTrigger />
      <Separator
        orientation="vertical"
        className="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1">{title}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  </header>
)

export const DocumentDetailPage = () => {
  const { documentId } = documentDetailRoute.useParams()
  const search = documentDetailRoute.useSearch()
  const documentQuery = useDocumentQuery(documentId)
  const document = documentQuery.data
  const page = typeof search?.page === 'number' ? search.page : null
  const previewQuery = useDocumentPreviewQuery(document?.id, page)

  return (
    <>
      <DocumentHeader title={document?.file_name ?? undefined} />
      <div className="flex flex-1 flex-col p-4">
        <div className="max-w-5xl mx-auto w-full flex flex-col rounded-lg border h-[calc(100vh-6rem)]">
          {!document || documentQuery.isLoading ? (
            <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
              <Loader2Icon className="size-4 animate-spin" /> Loading
              document...
            </div>
          ) : (
            <div className="flex-1 overflow-hidden">
              {previewQuery.data && (
                <iframe
                  title={document.file_name}
                  src={previewQuery.data}
                  className="w-full h-full"
                />
              )}

              {previewQuery.isLoading && (
                <div className="flex h-full items-center justify-center text-muted-foreground gap-2">
                  <Loader2Icon className="size-4 animate-spin" /> Loading
                  preview...
                </div>
              )}

              {previewQuery.isError && (
                <div className="flex h-full items-center justify-center text-muted-foreground gap-2">
                  <FileIcon className="size-5" />
                  <span>Failed to load preview</span>
                </div>
              )}

              {!previewQuery.data && (
                <div className="flex h-full items-center justify-center text-muted-foreground gap-2">
                  <FileIcon className="size-5" />
                  <span>No preview available</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
