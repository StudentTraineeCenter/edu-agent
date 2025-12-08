import { mindMapDetailRoute } from '@/routes/_config'
import { MindMapDetailPage } from '@/features/mind-map/mind-map-detail-page'

export const MindMapDetailRoute = () => {
  const params = mindMapDetailRoute.useParams()
  return (
    <MindMapDetailPage
      mindMapId={params.mindMapId}
      projectId={params.projectId}
    />
  )
}
