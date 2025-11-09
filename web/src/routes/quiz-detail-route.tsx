import { quizDetailRoute } from './_config'
import { QuizDetailPage } from '@/features/quiz/quiz-detail-page'

export const QuizDetailRoute = () => {
  const params = quizDetailRoute.useParams()
  return <QuizDetailPage projectId={params.projectId} quizId={params.quizId} />
}
