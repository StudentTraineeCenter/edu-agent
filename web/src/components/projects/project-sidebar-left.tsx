import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import { ProjectChatList } from './project-chat-list'
import { ProjectDocumentList } from './project-document-list'
import type { Chat, Document, Project } from '@/integrations/api'

type Props = React.ComponentProps<typeof Sidebar> & {
  project: Pick<Project, 'id' | 'name'>
  chats: Chat[]
  documents: Document[]
  onSelectChatId: (chatId: string) => void
  onSelectDocumentId?: (documentId: string) => void
}

export function ProjectSidebarLeft({
  chats,
  documents,
  onSelectChatId,
  onSelectDocumentId,
  project,
  ...props
}: Props) {
  return (
    <Sidebar className="border-r-0" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <span className="text-lg font-bold">{project.name}</span>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <ProjectChatList
          projectId={project.id}
          chats={chats}
          onSelectChatId={onSelectChatId}
        />
        <ProjectDocumentList
          documents={documents}
          onSelectDocumentId={onSelectDocumentId}
        />
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
