import { CreateProjectDialog } from '@/components/projects/create-project-dialog'

export const ModalProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      <CreateProjectDialog />
      {children}
    </>
  )
}
