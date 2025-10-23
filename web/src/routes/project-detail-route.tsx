import { ProjectSidebarLeft } from '@/components/projects/project-sidebar-left'
import { ProjectSidebarRight } from '@/components/projects/project-sidebar-right'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { projectDetailRoute } from '@/routes/_config'
import { useChatsQuery } from '@/data-acess/chat'
import { useDocumentsQuery } from '@/data-acess/document'
import { useProjectQuery } from '@/data-acess/project'
import { Outlet, useNavigate } from '@tanstack/react-router'
import type { Chat, Document, Project } from '@/integrations/api'

const ProjectLayout = ({
  project,
  chats,
  documents,
  onSelectChatId,
  onSelectDocumentId,
  onSelectMaterialId,
  onCreateFlashcard,
  onCreateQuiz,
  children,
}: {
  project: Project | null
  chats: Chat[]
  documents: Document[]
  onSelectChatId: (chatId: string) => void
  onSelectDocumentId: (documentId: string) => void
  onSelectMaterialId: (materialId: string) => void
  onCreateFlashcard: () => void
  onCreateQuiz: () => void
  children: React.ReactNode
}) => (
  <SidebarProvider>
    {project && (
      <ProjectSidebarLeft
        project={project}
        chats={chats}
        documents={documents}
        onSelectChatId={onSelectChatId}
        onSelectDocumentId={onSelectDocumentId}
      />
    )}
    <SidebarInset>{children}</SidebarInset>
    {project && (
      <ProjectSidebarRight
        projectId={project.id}
        onSelectMaterialId={onSelectMaterialId}
        onCreateFlashcard={onCreateFlashcard}
        onCreateQuiz={onCreateQuiz}
      />
    )}
  </SidebarProvider>
)

export const ProjectDetailPage = () => {
  const params = projectDetailRoute.useParams()
  const navigate = useNavigate()

  const chatsQuery = useChatsQuery(params.projectId)
  const chats = chatsQuery.data?.data ?? []

  const projectQuery = useProjectQuery(params.projectId)
  const project = projectQuery.data ?? null

  const documentsQuery = useDocumentsQuery(params.projectId)
  const documents = documentsQuery.data?.data ?? []

  const handleSelectChatId = (chatId: string) => {
    navigate({
      to: '/projects/$projectId/chats/$chatId',
      params: { projectId: params.projectId, chatId },
    })
  }

  const handleSelectDocumentId = (documentId: string) => {
    navigate({
      to: '/projects/$projectId/documents/$documentId',
      params: { projectId: params.projectId, documentId },
    })
  }

  const handleSelectMaterialId = (materialId: string) => {
    // TODO: Navigate to material detail page
    console.log('Selected material:', materialId)
  }

  const handleCreateFlashcard = () => {
    // TODO: Open flashcard creation dialog
    console.log('Create flashcard')
  }

  const handleCreateQuiz = () => {
    // TODO: Open quiz creation dialog
    console.log('Create quiz')
  }

  return (
    <ProjectLayout
      project={project}
      chats={chats}
      documents={documents}
      onSelectChatId={handleSelectChatId}
      onSelectDocumentId={handleSelectDocumentId}
      onSelectMaterialId={handleSelectMaterialId}
      onCreateFlashcard={handleCreateFlashcard}
      onCreateQuiz={handleCreateQuiz}
    >
      <Outlet />
    </ProjectLayout>
  )
}
