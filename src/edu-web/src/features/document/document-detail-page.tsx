import { Loader2Icon } from 'lucide-react'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { DocumentHeader } from './components/document-header'
import { documentPreviewAtom } from '@/data-acess/document'

type DocumentContentProps = {
  documentId: string
  projectId: string
}

const DocumentContent = ({ projectId, documentId }: DocumentContentProps) => {
  const previewResult = useAtomValue(
    documentPreviewAtom({ projectId, documentId }),
  )

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
            <iframe
              src={preview.preview_url}
              className="w-full h-full border-0"
              title="Document preview"
            />
          ))
          .render()}
      </div>
    </div>
  )
}

type DocumentDetailPageProps = {
  documentId: string
  projectId: string
}

export const DocumentDetailPage = ({
  documentId,
  projectId,
}: DocumentDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <DocumentHeader documentId={documentId} projectId={projectId} />
      <DocumentContent projectId={projectId} documentId={documentId} />
    </div>
  )
}
