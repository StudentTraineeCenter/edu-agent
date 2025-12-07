import { MindMapHeader } from './components/mind-map-header'
import { MindMapContent } from './components/mind-map-content'

type MindMapDetailPageProps = {
  projectId: string
  mindMapId: string
}

export const MindMapDetailPage = ({
  projectId,
  mindMapId,
}: MindMapDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <MindMapHeader projectId={projectId} mindMapId={mindMapId} />

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="max-w-7xl mx-auto w-full flex flex-col flex-1 min-h-0 p-4">
          <MindMapContent mindMapId={mindMapId} className="flex-1" />
        </div>
      </div>
    </div>
  )
}
