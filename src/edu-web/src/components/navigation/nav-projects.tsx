import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from '@/components/ui/sidebar'
import { chatsAtom } from '@/data-acess/chat'
import { currentProjectIdAtom, projectsAtom } from '@/data-acess/project'
import { useCreateProjectDialog } from '@/features/project/components/upsert-project-dialog'
import type { ChatDto } from '@/integrations/api/client'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Link } from '@tanstack/react-router'
import { Cause } from 'effect'
import { ChevronRightIcon, FolderIcon, PlusIcon } from 'lucide-react'

const ChatItem = ({ chat }: { chat: ChatDto }) => {
  return (
    <SidebarMenuSubItem key={chat.id}>
      <SidebarMenuSubButton asChild size="md">
        <Link
          to="/dashboard/p/$projectId/c/$chatId"
          params={{
            projectId: chat.project_id,
            chatId: chat.id,
          }}
        >
          <span>{chat.title ?? "Unnamed Chat"}</span>
        </Link>
      </SidebarMenuSubButton>
    </SidebarMenuSubItem>
  )
}

const ChatList = ({ projectId }: { projectId: string }) => {
  const chatsResult = useAtomValue(chatsAtom(projectId))

  return Result.builder(chatsResult)
    .onSuccess((chats) => (
      <>
        {chats.map((chat) => (
          <ChatItem key={chat.id} chat={chat} />
        ))}

        {chats.length === 0 && (
          <SidebarMenuSubItem>
            <SidebarMenuSubButton size="md">
              <span className="text-sm text-muted-foreground">
                No chats yet
              </span>
            </SidebarMenuSubButton>
          </SidebarMenuSubItem>
        )}
      </>
    ))
    .onInitialOrWaiting(() => (
      <SidebarMenuSubItem>
        <SidebarMenuSubButton size="md">
          <span className="text-sm text-muted-foreground">Loading...</span>
        </SidebarMenuSubButton>
      </SidebarMenuSubItem>
    ))
    .onFailure((cause) => (
      <SidebarMenuSubItem>
        <SidebarMenuSubButton size="md">
          <span className="text-sm text-muted-foreground">
            Error: {Cause.pretty(cause)}
          </span>
        </SidebarMenuSubButton>
      </SidebarMenuSubItem>
    ))
    .render()
}

export function NavProjects() {
  const projectsResult = useAtomValue(projectsAtom)

  const currentProjectId = useAtomValue(currentProjectIdAtom)
  const openCreateProjectDialog = useCreateProjectDialog((state) => state.open)

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel>Projects</SidebarGroupLabel>
      <SidebarMenu>
        <SidebarMenuButton
          tooltip="New project"
          onClick={() => openCreateProjectDialog()}
        >
          <PlusIcon className="size-4 opacity-70" />
          <span>New project</span>
        </SidebarMenuButton>

        {Result.builder(projectsResult)
          .onSuccess((projects) => (
            <>
              {projects.map((project) => {
                const isActive = project.id === currentProjectId
                if (isActive) {
                  return (
                    <Collapsible
                      key={project.id}
                      asChild
                      defaultOpen={isActive}
                      className="group/collapsible"
                    >
                      <SidebarMenuItem>
                        <CollapsibleTrigger asChild>
                          <SidebarMenuButton tooltip={project.name} asChild>
                            <Link
                              to="/dashboard/p/$projectId"
                              params={{ projectId: project.id }}
                            >
                              <FolderIcon className="size-4 opacity-70" />
                              <span>{project.name}</span>
                              <ChevronRightIcon className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                            </Link>
                          </SidebarMenuButton>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <SidebarMenuSub>
                            <ChatList projectId={project.id} />
                          </SidebarMenuSub>
                        </CollapsibleContent>
                      </SidebarMenuItem>
                    </Collapsible>
                  )
                } else {
                  return (
                    <SidebarMenuItem key={project.id}>
                      <SidebarMenuButton asChild>
                        <Link
                          to="/dashboard/p/$projectId"
                          params={{ projectId: project.id }}
                        >
                          <FolderIcon className="size-4 opacity-70" />
                          <span>{project.name}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                }
              })}
            </>
          ))
          .render()}
      </SidebarMenu>
    </SidebarGroup>
  )
}

export default NavProjects
