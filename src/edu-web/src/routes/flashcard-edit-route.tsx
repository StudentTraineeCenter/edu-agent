import { flashcardEditRoute } from '@/routes/_config'
import { FlashcardEditPage } from '@/features/flashcard/flashcard-edit-page'

export const FlashcardEditRoute = () => {
  const params = flashcardEditRoute.useParams()
  return (
    <FlashcardEditPage
      flashcardGroupId={params.flashcardGroupId}
      projectId={params.projectId}
    />
  )
}
