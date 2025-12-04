import { studySessionDetailRoute } from './_config'
import { StudySessionDetailPage } from '@/features/adaptive-learning/study-session-detail-page'

export const StudySessionDetailRoute = () => {
  const params = studySessionDetailRoute.useParams()
  return (
    <StudySessionDetailPage
      sessionId={params.sessionId}
      projectId={params.projectId}
    />
  )
}
