import { studyPlanDetailRoute } from './_config'
import { StudyPlanDetailPage } from '@/features/study-plan/study-plan-detail-page'

export const StudyPlanDetailRoute = () => {
  const params = studyPlanDetailRoute.useParams()
  return <StudyPlanDetailPage projectId={params.projectId} />
}

