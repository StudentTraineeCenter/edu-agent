import { StudyPlanPage } from '@/features/study-plan/study-plan-page'
import { studyPlanRoute } from '@/routes/_config'

export const StudyPlanRoute = () => {
  const params = studyPlanRoute.useParams()
  return <StudyPlanPage projectId={params.projectId} />
}
