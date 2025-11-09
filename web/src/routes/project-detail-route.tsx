import { projectDetailRoute } from './_config'
import { ProjectDetailPage } from '@/features/project/project-detail-page'

export const ProjectDetailRoute = () => {
  const params = projectDetailRoute.useParams()
  return <ProjectDetailPage projectId={params.projectId} />
}
