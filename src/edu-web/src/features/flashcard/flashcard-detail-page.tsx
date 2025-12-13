import { FlashcardDetail } from './components/flashcard-detail'
import { FlashcardHeader } from './components/flashcard-header'

type FlashcardDetailPageProps = {
  flashcardGroupId: string
  projectId: string
}

export const FlashcardDetailPage = ({
  flashcardGroupId,
  projectId,
}: FlashcardDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <FlashcardHeader
        flashcardGroupId={flashcardGroupId}
        projectId={projectId}
      />

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="max-w-5xl mx-auto w-full flex flex-col flex-1 min-h-0">
          <FlashcardDetail
            flashcardGroupId={flashcardGroupId}
            className="flex-1"
          />
        </div>
      </div>
    </div>
  )
}
