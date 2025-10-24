import { EditChatDialog } from '@/components/chats/edit-chat-dialog'
import { UpsertProjectDialog } from '@/components/projects/upsert-project-dialog'
import { FlashcardDialog } from '@/components/flashcards/flashcard-dialog'

export const ModalProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      <UpsertProjectDialog />
      <EditChatDialog />
      <FlashcardDialog />
      {children}
    </>
  )
}
