import { quizEditRoute } from '@/routes/_config'
import { QuizEditPage } from '@/features/quiz/quiz-edit-page'

export const QuizEditRoute = () => {
  const params = quizEditRoute.useParams()
  return <QuizEditPage quizId={params.quizId} projectId={params.projectId} />
}
