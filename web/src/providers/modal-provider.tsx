import { EditChatDialog } from '@/features/chat/components/edit-chat-dialog'
import { UpsertProjectDialog } from '@/features/project/components/upsert-project-dialog'
import { UploadDocumentDialog } from '@/features/document/components/upload-document-dialog'

export const ModalProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      <UpsertProjectDialog />
      <EditChatDialog />
      <UploadDocumentDialog />
      {children}
    </>
  )
}
