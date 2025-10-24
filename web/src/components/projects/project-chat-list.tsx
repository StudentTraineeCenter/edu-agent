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
import { useEditChatDialog } from '@/components/chats/edit-chat-dialog'

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

  const openEditChatDialog = useEditChatDialog().open

  const createChatMutation = useCreateChatMutation({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [projectId, 'chats'] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  const handleSelect = useCallback(
    (chatId: string) => {
      onSelectChatId(chatId)
    },
    [onSelectChatId],
  )

  const handleAdd = useCallback(async () => {
    const chat = await createChatMutation.mutateAsync({ project_id: projectId })
    if (!chat) return

    onSelectChatId(chat.id)
  }, [createChatMutation, projectId])

  const handleEdit = useCallback((chatId: string) => {
    const chat = chats.find((chat) => chat.id === chatId)
    if (!chat) return

    openEditChatDialog(chatId, chat.title)
  }, [openEditChatDialog, chats])

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
                  <DropdownMenuItem onClick={() => handleEdit(chat.id)}>
                    <span>Edit</span>
                  </DropdownMenuItem>
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
