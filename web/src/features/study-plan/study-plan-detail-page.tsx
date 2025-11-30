import { StudyPlanHeader } from './components/study-plan-header'
import { StudyPlanContent } from './components/study-plan-content'

type StudyPlanDetailPageProps = {
  projectId: string
}

export const StudyPlanDetailPage = ({
  projectId,
}: StudyPlanDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <StudyPlanHeader projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="max-w-5xl mx-auto w-full flex flex-col flex-1 min-h-0 p-4">
          <StudyPlanContent projectId={projectId} className="flex-1" />
        </div>
      </div>
    </div>
  )
}

