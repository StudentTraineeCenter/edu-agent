import { QuizDetail } from './components/quiz-detail'
import { QuizHeader } from './components/quiz-header'

type QuizDetailPageProps = {
  projectId: string
  quizId: string
}

export const QuizDetailPage = ({ projectId, quizId }: QuizDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <QuizHeader quizId={quizId} projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="max-w-5xl mx-auto w-full flex flex-col flex-1 min-h-0">
          <QuizDetail
            quizId={quizId}
            projectId={projectId}
            className="flex-1"
          />
        </div>
      </div>
    </div>
  )
}
