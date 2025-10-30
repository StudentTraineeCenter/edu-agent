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
import {
  FileIcon,
  FileTextIcon,
  Loader2Icon,
  MoreHorizontal,
  PlusIcon,
} from 'lucide-react'
import { truncate } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { documentsAtom } from '@/data-acess/document'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { useNavigate } from '@tanstack/react-router'
import type { DocumentDto } from '@/integrations/api/client'
import { currentProjectIdAtom } from '@/data-acess/project'

type Props = React.ComponentProps<typeof SidebarGroup>

const DocumentItem = ({ document }: { document: DocumentDto }) => {
  const navigate = useNavigate()
  const currentProjectId = useAtomValue(currentProjectIdAtom)

  const handleSelectDocument = (documentId: string) => {
    if (!currentProjectId) return
    navigate({
      to: '/projects/$projectId/documents/$documentId',
      params: { projectId: currentProjectId, documentId },
    })
  }

  const getIcon = (fileType: string) => {
    switch (fileType) {
      case 'pdf':
        return <FileIcon className="size-4" />
      case 'docx':
        return <FileTextIcon className="size-4" />
      case 'doc':
        return <FileTextIcon className="size-4" />
      case 'txt':
        return <FileTextIcon className="size-4" />
      case 'rtf':
        return <FileTextIcon className="size-4" />
    }
  }

  return (
    <SidebarMenuItem key={document.id}>
      <SidebarMenuButton
        tooltip={document.file_name}
        onClick={() => handleSelectDocument(document.id)}
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
  )
}

export const ProjectDocumentList = ({ ...props }: Props) => {
  const currentProjectId = useAtomValue(currentProjectIdAtom)
  const documentsResult = useAtomValue(documentsAtom(currentProjectId ?? ''))

  const handleAdd = () => {
    // TODO: Implement add document
  }

  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>Documents</SidebarGroupLabel>
      <SidebarGroupAction title="Add Documents" onClick={handleAdd}>
        <PlusIcon />
        <span className="sr-only">Add Documents</span>
      </SidebarGroupAction>
      <SidebarGroupContent>
        <SidebarMenu>
          {Result.builder(documentsResult)
            .onInitialOrWaiting(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
                <Loader2Icon className="size-4 animate-spin" />
                <span>Loading documents...</span>
              </div>
            ))
            .onFailure(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
                <span>Failed to load documents</span>
              </div>
            ))
            .onSuccess((documents) => (
              <>
                {documents.map((document) => (
                  <DocumentItem key={document.id} document={document} />
                ))}
              </>
            ))
            .render()}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
