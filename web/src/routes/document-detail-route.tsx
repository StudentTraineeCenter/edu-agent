import { documentAtom, documentPreviewAtom } from '@/data-acess/document'
import { documentDetailRoute } from '@/routes/_config'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Loader2Icon } from 'lucide-react'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'

const DocumentHeader = ({ title }: { title?: string }) => (
  <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
    <div className="flex flex-1 items-center gap-2 px-3">
      <SidebarTrigger />
      <Separator
        orientation="vertical"
        className="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {title}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  </header>
)

export const DocumentDetailPage = () => {
  const { documentId } = documentDetailRoute.useParams()

  const documentResult = useAtomValue(documentAtom(documentId))
  const previewResult = useAtomValue(documentPreviewAtom(documentId))

  return (
    <div className="flex h-full flex-col">
      {Result.builder(documentResult)
        .onSuccess((document) => (
          <DocumentHeader title={document.file_name ?? 'Untitled document'} />
        ))
        .onInitialOrWaiting(() => (
          <div className="h-14 shrink-0">
            <Skeleton className="w-72 h-7 mt-3 ml-4" />
          </div>
        ))
        .render()}

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="mx-auto w-full flex flex-col flex-1 min-h-0">
          {Result.builder(previewResult)
            .onInitialOrWaiting(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
                <Loader2Icon className="size-4 animate-spin" />
                <span>Loading preview...</span>
              </div>
            ))
            .onFailure(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
                <span>Failed to load preview</span>
              </div>
            ))
            .onSuccess((preview) => (
              <object
                data={preview}
                type="application/pdf"
                className="w-full h-full"
              >
                <p>
                  Your browser doesn't support PDF viewing.
                  <a href={preview} target="_blank" rel="noopener noreferrer">
                    Click here to download the PDF
                  </a>
                </p>
              </object>
            ))
            .render()}
        </div>
      </div>
    </div>
  )
}
