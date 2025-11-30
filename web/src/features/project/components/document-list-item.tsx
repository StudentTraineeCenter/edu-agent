import { Link } from '@tanstack/react-router'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  FileIcon,
  Loader2Icon,
  CheckCircle2Icon,
  XCircleIcon,
  MoreVerticalIcon,
  TrashIcon,
  type LucideIcon,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useAtomSet } from '@effect-atom/atom-react'
import { deleteDocumentAtom } from '@/data-acess/document'
import { DocumentStatus } from '@/integrations/api/client'
import { cn } from '@/lib/utils'
import type { DocumentDto } from '@/integrations/api/client'
import { useConfirmationDialog } from '@/components/confirmation-dialog'

type Props = {
  document: DocumentDto
}

const getDocumentStatus = (
  status: typeof DocumentStatus.Type,
): {
  label: string
  variant: 'default' | 'secondary' | 'destructive' | 'outline'
  icon: LucideIcon
} => {
  switch (status) {
    case 'uploaded':
    case 'processing':
      return {
        label: 'In progress',
        variant: 'secondary',
        icon: Loader2Icon,
      }
    case 'processed':
    case 'indexed':
      return {
        label: 'Ready',
        variant: 'default',
        icon: CheckCircle2Icon,
      }
    case 'failed':
      return {
        label: 'Failed',
        variant: 'destructive',
        icon: XCircleIcon,
      }
    default:
      return {
        label: 'In progress',
        variant: 'secondary',
        icon: Loader2Icon,
      }
  }
}

export const DocumentListItem = ({ document }: Props) => {
  const statusInfo = getDocumentStatus(document.status)
  const StatusIcon = statusInfo.icon

  const deleteDocument = useAtomSet(deleteDocumentAtom, { mode: 'promise' })
  const confirmationDialog = useConfirmationDialog()

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const confirmed = await confirmationDialog.open({
      title: 'Delete Document',
      description: `Are you sure you want to delete "${document.file_name}"? This action cannot be undone.`,
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    })

    if (confirmed) {
      await deleteDocument({
        documentId: document.id,
        projectId: document.project_id ?? '',
      })
    }
  }

  return (
    <li className="rounded-md p-3 hover:bg-muted/50 group">
      <div className="flex items-center gap-2">
        <Link
          to="/dashboard/p/$projectId/d/$documentId"
          params={{
            projectId: document.project_id ?? '',
            documentId: document.id,
          }}
          className="flex-1"
        >
          <div className="flex items-center gap-3 min-w-0">
            <FileIcon className="size-4 flex-shrink-0" />
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="truncate flex-1 min-w-0">
                  {document.file_name}
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p>{document.file_name}</p>
              </TooltipContent>
            </Tooltip>
            <Badge variant={statusInfo.variant} className="gap-1 flex-shrink-0">
              <StatusIcon
                className={cn(
                  'size-3',
                  statusInfo.variant === 'secondary' && 'animate-spin',
                )}
              />
              {statusInfo.label}
            </Badge>
            <span className="text-xs text-muted-foreground flex-shrink-0">
              {format(new Date(document.uploaded_at), 'MM/dd HH:mm')}
            </span>
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
