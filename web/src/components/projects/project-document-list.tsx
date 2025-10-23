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
import { FileIcon, MoreHorizontal, PlusIcon } from 'lucide-react'
import { truncate } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import type { Document } from '@/integrations/api'

type Props = React.ComponentProps<typeof SidebarGroup> & {
  documents: Document[]
  onAdd?: () => void
  onSelectDocumentId?: (documentId: string) => void
}

const getIcon = (fileType: string) => {
  switch (fileType) {
    case 'pdf':
      return <FileIcon />
  }
}

export const ProjectDocumentList = ({
  documents,
  onAdd,
  onSelectDocumentId,
  ...props
}: Props) => {
  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>Documents</SidebarGroupLabel>
      <SidebarGroupAction title="Add Documents" onClick={onAdd}>
        <PlusIcon />
        <span className="sr-only">Add Documents</span>
      </SidebarGroupAction>
      <SidebarGroupContent>
        <SidebarMenu>
          {documents.map((document) => (
            <SidebarMenuItem key={document.id}>
              <SidebarMenuButton
                tooltip={document.file_name}
                onClick={() => onSelectDocumentId?.(document.id)}
              >
                {getIcon(document.file_type)}
                {truncate(document.file_name, 20)}
              </SidebarMenuButton>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction>
                    <MoreHorizontal />
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="right" align="start">
                  <DropdownMenuItem variant="destructive">
                    <span>Delete Document</span>
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
