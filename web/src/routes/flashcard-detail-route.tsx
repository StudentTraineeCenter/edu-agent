import { flashcardDetailRoute } from './_config'
import { FlashcardDetailPage } from '@/features/flashcard/flashcard-detail-page'

export const FlashcardDetailRoute = () => {
  const params = flashcardDetailRoute.useParams()
  return <FlashcardDetailPage flashcardGroupId={params.flashcardGroupId} />
}
