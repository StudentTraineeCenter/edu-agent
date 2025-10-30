import { Loader2Icon, MoreHorizontalIcon, PlusIcon } from 'lucide-react'
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
import { truncate } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { createChatAtom, chatsAtom } from '@/data-acess/chat'
import { useCallback } from 'react'
import { useEditChatDialog } from '@/components/chats/edit-chat-dialog'
import { Result, useAtom, useAtomValue } from '@effect-atom/atom-react'
import { useNavigate } from '@tanstack/react-router'
import type { ChatDto } from '@/integrations/api/client'
import { currentProjectIdAtom } from '@/data-acess/project'

type Props = React.ComponentProps<typeof SidebarGroup>

const ChatItem = ({ chat }: { chat: ChatDto }) => {
  const currentProjectId = useAtomValue(currentProjectIdAtom)
  const navigate = useNavigate()
  const { open: openEditChatDialog } = useEditChatDialog()

  const handleSelect = () => {
    if (!currentProjectId) return

    navigate({
      to: '/projects/$projectId/chats/$chatId',
      params: { projectId: currentProjectId, chatId: chat.id },
    })
  }

  const handleEdit = () => {
    openEditChatDialog(chat.id, chat.title)
  }

  return (
    <SidebarMenuItem key={chat.id}>
      <SidebarMenuButton
        onClick={handleSelect}
        tooltip={chat.title ?? 'Untitled Chat'}
      >
        <span>{truncate(chat.title ?? 'Untitled Chat', 20)}</span>
      </SidebarMenuButton>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <SidebarMenuAction>
            <MoreHorizontalIcon />
          </SidebarMenuAction>
        </DropdownMenuTrigger>
        <DropdownMenuContent side="right" align="start">
          <DropdownMenuItem onClick={handleEdit}>
            <span>Edit</span>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <span>Archive</span>
          </DropdownMenuItem>
          <DropdownMenuItem variant="destructive">
            <span>Delete</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  )
}

export const ProjectChatList = ({ ...props }: Props) => {
  const navigate = useNavigate()
  const currentProjectId = useAtomValue(currentProjectIdAtom)

  const [createChatResult, createChatMutation] = useAtom(createChatAtom, {
    mode: 'promise',
  })

  const chatsResult = useAtomValue(chatsAtom(currentProjectId ?? ''))

  const handleAdd = useCallback(async () => {
    if (!currentProjectId) return

    const chat = await createChatMutation({
      project_id: currentProjectId,
    })

    navigate({
      to: '/projects/$projectId/chats/$chatId',
      params: { projectId: currentProjectId, chatId: chat.id },
    })
  }, [createChatMutation, currentProjectId, navigate])

  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>Chats</SidebarGroupLabel>
      <SidebarGroupAction title="Add Chat" onClick={handleAdd}>
        {Result.builder(createChatResult)
          .onWaiting(() => <Loader2Icon className="size-4 animate-spin" />)
          .orElse(() => (
            <>
              <PlusIcon />
              <span className="sr-only">Add Chat</span>
            </>
          ))}
      </SidebarGroupAction>
      <SidebarGroupContent>
        <SidebarMenu>
          {Result.builder(chatsResult)
            .onInitialOrWaiting(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
                <Loader2Icon className="size-4 animate-spin" />
                <span>Loading chats...</span>
              </div>
            ))
            .onFailure(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
                <span>Failed to load chats</span>
              </div>
            ))
            .onSuccess((chats) => (
              <>
                {chats.map((chat) => (
                  <ChatItem key={chat.id} chat={chat} />
                ))}
              </>
            ))
            .render()}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
