import { ProjectSidebarLeft } from '@/components/projects/project-sidebar-left'
import { ProjectSidebarRight } from '@/components/projects/project-sidebar-right'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { projectDetailRoute } from '@/routes/_config'
import { useChatsQuery } from '@/data-acess/chat'
import { useDocumentsQuery } from '@/data-acess/document'
import { useMeQuery } from '@/data-acess/auth'
import { useProjectQuery } from '@/data-acess/project'
import { Outlet, useNavigate } from '@tanstack/react-router'
import type { Chat, Document, Project, User } from '@/integrations/api'

const ProjectLayout = ({
  project,
  chats,
  documents,
  user,
  onSelectChatId,
  onSelectDocumentId,
  children,
}: {
  project: Project | null
  chats: Chat[]
  documents: Document[]
  user: User | null
  onSelectChatId: (chatId: string) => void
  onSelectDocumentId: (documentId: string) => void
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
    {user && <ProjectSidebarRight materials={[]} user={user} />}
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

  const meQuery = useMeQuery()
  const me = meQuery.data ?? null

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

  return (
    <ProjectLayout
      project={project}
      chats={chats}
      documents={documents}
      user={me}
      onSelectChatId={handleSelectChatId}
      onSelectDocumentId={handleSelectDocumentId}
    >
      <Outlet />
    </ProjectLayout>
  )
}
