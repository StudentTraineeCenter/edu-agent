import { EditChatDialog } from '@/components/chats/edit-chat-dialog'
import { CreateProjectDialog } from '@/components/projects/create-project-dialog'

export const ModalProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      <CreateProjectDialog />
      <EditChatDialog />
      {children}
    </>
  )
}
