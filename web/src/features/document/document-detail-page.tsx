import { documentPreviewAtom } from '@/data-acess/document'
import { Loader2Icon } from 'lucide-react'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { DocumentHeader } from './components/document-header'

type DocumentContentProps = {
  documentId: string
}

const DocumentContent = ({ documentId }: DocumentContentProps) => {
  const previewResult = useAtomValue(documentPreviewAtom(documentId))

  return (
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
  )
}

type DocumentDetailPageProps = {
  documentId: string
}

export const DocumentDetailPage = ({ documentId }: DocumentDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <DocumentHeader documentId={documentId} />
      <DocumentContent documentId={documentId} />
    </div>
  )
}
