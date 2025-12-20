import { useConfirmationDialog } from '@/components/confirmation-dialog'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { deleteChatAtom } from '@/data-acess/chat'
import type { ChatDto } from '@/integrations/api/client'
import { useAtomSet } from '@effect-atom/atom-react'
import { Link } from '@tanstack/react-router'
import { format } from 'date-fns'
import { MoreVerticalIcon, TrashIcon } from 'lucide-react'

type Props = {
  chat: ChatDto
}

export const ChatListItem = ({ chat }: Props) => {
  const deleteChat = useAtomSet(deleteChatAtom, { mode: 'promise' })
  const confirmationDialog = useConfirmationDialog()

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const confirmed = await confirmationDialog.open({
      title: 'Delete Chat',
      description: `Are you sure you want to delete "${chat.title ?? 'Untitled chat'}"? This action cannot be undone.`,
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    })

    if (confirmed) {
      await deleteChat({
        chatId: chat.id,
        projectId: chat.project_id,
      })
    }
  }

  return (
    <li className="rounded-md p-3 hover:bg-muted/50 group">
      <div className="flex items-center gap-2">
        <Link
          to="/dashboard/p/$projectId/c/$chatId"
          params={{
            projectId: chat.project_id,
            chatId: chat.id,
          }}
          className="flex-1"
        >
          <div className="grid grid-cols-6 items-center">
            <div className="flex flex-col w-full col-span-5 overflow-hidden">
              <span className="truncate">{chat.title ?? 'Untitled chat'}</span>
              {chat.last_message_content && (
                <span className="text-xs text-muted-foreground truncate">
                  {chat.last_message_content}
                </span>
              )}
            </div>
            <div className="flex flex-col col-span-1 text-right pl-2">
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {format(
                  new Date(chat.last_message_at ?? chat.updated_at),
                  'MM/dd',
                )}
              </span>
            </div>
          </div>
        </Link>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreVerticalIcon className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleDelete} variant="destructive">
              <TrashIcon className="size-4" />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </li>
  )
}
