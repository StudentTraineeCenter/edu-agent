import { MoreHorizontal, PlusIcon } from 'lucide-react'
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
} from '@/components/ui/sidebar'
import type { Chat } from '@/integrations/api'
import { truncate } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { useCreateChatMutation } from '@/data-acess/chat'
import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'

type Props = React.ComponentProps<typeof SidebarGroup> & {
  projectId: string
  chats: Chat[]
  onSelectChatId: (chatId: string) => void
}

export const ProjectChatList = ({
  projectId,
  chats,
  onSelectChatId,
  ...props
}: Props) => {
  const queryClient = useQueryClient()

  const createChatMutation = useCreateChatMutation({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  const handleSelect = useCallback(
    (chatId: string) => {
      onSelectChatId(chatId)
    },
    [onSelectChatId],
  )

  const handleAdd = useCallback(() => {
    createChatMutation.mutate({ project_id: projectId })
  }, [createChatMutation, projectId])

  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>Chats</SidebarGroupLabel>
      <SidebarGroupAction title="Add Chat" onClick={handleAdd}>
        <PlusIcon />
        <span className="sr-only">Add Chat</span>
      </SidebarGroupAction>
      <SidebarGroupContent>
        <SidebarMenu>
          {chats.map((chat) => (
            <SidebarMenuItem key={chat.id}>
              <SidebarMenuButton
                onClick={() => handleSelect(chat.id)}
                tooltip={chat.title ?? 'Untitled Chat'}
              >
                <span>{truncate(chat.title ?? 'Untitled Chat', 20)}</span>
              </SidebarMenuButton>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction>
                    <MoreHorizontal />
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="right" align="start">
                  <DropdownMenuItem>
                    <span>Archive Chat</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem variant="destructive">
                    <span>Delete Chat</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
