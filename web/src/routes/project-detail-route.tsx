import { currentProjectIdAtom, projectAtom } from '@/data-acess/project'
import { projectDetailRoute } from '@/routes/_config'
import { Link, useNavigate } from '@tanstack/react-router'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { useEffect, useMemo } from 'react'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { chatsAtom, createChatAtom } from '@/data-acess/chat'
import { ChatDto, DocumentDto, DocumentStatus } from '@/integrations/api/client'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  BrainCircuitIcon,
  FileIcon,
  ListChecksIcon,
  PlusIcon,
  Loader2Icon,
  CheckCircle2Icon,
  XCircleIcon,
  type LucideIcon,
} from 'lucide-react'
import { format } from 'date-fns'
import { documentsAtom } from '@/data-acess/document'
import { Material, materialsAtom } from '@/data-acess/materials'
import { useUploadDocumentDialog } from '@/components/documents/upload-document-dialog'
import { cn } from '@/lib/utils'
import { Data, Match } from 'effect'

const ProjectHeader = ({ title }: { title: string }) => {
  return (
    <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        <SidebarTrigger />
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage className="line-clamp-1 font-medium">
                {title}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
  )
}

const ChatListItem = ({ chat }: { chat: ChatDto }) => {
  const lastMessageContent = useMemo(() => {
    const value = chat.last_message?.content ?? 'No messages yet'
    return value.length > 100 ? value.slice(0, 100) + '...' : value
  }, [chat.last_message])

  return (
    <li className="rounded-md p-3 hover:bg-muted/50">
      <Link
        to="/projects/$projectId/chats/$chatId"
        params={{
          projectId: chat.project_id,
          chatId: chat.id,
        }}
      >
        <div className="grid grid-cols-6 items-center">
          <div className="flex flex-col w-full col-span-5">
            <span>{chat.title ?? 'Untitled chat'}</span>
            <span className="text-sm text-muted-foreground">
              {lastMessageContent}
            </span>
          </div>
          <div className="flex flex-col col-span-1 text-right">
            <span className="text-xs text-muted-foreground">
              {format(new Date(chat.created_at), 'MM/dd HH:mm')}
            </span>
          </div>
        </div>
      </Link>
    </li>
  )
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

const DocumentListItem = ({ document }: { document: DocumentDto }) => {
  const statusInfo = getDocumentStatus(document.status)
  const StatusIcon = statusInfo.icon

  return (
    <li className="rounded-md p-3 hover:bg-muted/50">
      <Link
        to="/projects/$projectId/documents/$documentId"
        params={{
          projectId: document.project_id ?? '',
          documentId: document.id,
        }}
      >
        <div className="grid grid-cols-6 items-center">
          <div className="flex flex-col w-full col-span-5">
            <div className="flex items-center gap-2">
              <FileIcon className="size-4" />
              <span>{document.file_name}</span>
              <Badge variant={statusInfo.variant} className="gap-1">
                <StatusIcon
                  className={cn(
                    'size-3',
                    statusInfo.variant === 'secondary' && 'animate-spin',
                  )}
                />
                {statusInfo.label}
              </Badge>
            </div>
          </div>
          <div className="flex flex-col col-span-1 text-right">
            <span className="text-xs text-muted-foreground">
              {format(new Date(document.uploaded_at), 'MM/dd HH:mm')}
            </span>
          </div>
        </div>
      </Link>
    </li>
  )
}

const MaterialListItem = ({ material }: { material: Material }) => {
  const renderContent = ({
    name,
    created_at,
    icon: Icon,
  }: {
    name: string
    created_at: string
    icon: LucideIcon
  }) => {
    return (
      <div className="grid grid-cols-6 items-center">
        <div className="flex flex-col w-full col-span-5">
          <div className="flex items-center gap-2">
            <Icon className="size-4" />
            <span>{name}</span>
          </div>
        </div>
        <div className="flex flex-col col-span-1 text-right">
          <span className="text-xs text-muted-foreground">
            {format(new Date(created_at), 'MM/dd HH:mm')}
          </span>
        </div>
      </div>
    )
  }

  return Material.$match(material, {
    FlashcardGroup: ({ data: flashcardGroup }) => {
      return (
        <li className="rounded-md p-3 hover:bg-muted/50">
          <Link
            to="/projects/$projectId/flashcards/$flashcardGroupId"
            params={{
              projectId: flashcardGroup.project_id ?? '',
              flashcardGroupId: flashcardGroup.id,
            }}
          >
            {renderContent({
              name: flashcardGroup.name,
              created_at: flashcardGroup.created_at,
              icon: BrainCircuitIcon,
            })}
          </Link>
        </li>
      )
    },
    Quiz: ({ data: quiz }) => {
      return (
        <li className="rounded-md p-3 hover:bg-muted/50">
          <Link
            to="/projects/$projectId/quizzes/$quizId"
            params={{
              projectId: quiz.project_id ?? '',
              quizId: quiz.id,
            }}
          >
            {renderContent({
              name: quiz.name,
              created_at: quiz.created_at,
              icon: ListChecksIcon,
            })}
          </Link>
        </li>
      )
    },
  })
}

export const ProjectDetailPage = () => {
  const params = projectDetailRoute.useParams()
  const navigate = useNavigate()

  const projectResult = useAtomValue(projectAtom(params.projectId))
  const chatsResult = useAtomValue(chatsAtom(params.projectId))
  const documentsResult = useAtomValue(documentsAtom(params.projectId))
  const materialsResult = useAtomValue(materialsAtom(params.projectId))

  const setCurrentProject = useAtomSet(currentProjectIdAtom)
  const createChat = useAtomSet(createChatAtom, {
    mode: 'promise',
  })
  const openUploadDialog = useUploadDocumentDialog((state) => state.open)

  const handleCreateChat = async () => {
    const chat = await createChat({ project_id: params.projectId })
    navigate({
      to: '/projects/$projectId/chats/$chatId',
      params: { projectId: params.projectId, chatId: chat.id },
    })
  }

  const handleCreateDocument = () => {
    openUploadDialog(params.projectId)
  }

  useEffect(() => {
    setCurrentProject(params.projectId)
  }, [params.projectId])

  return (
    <>
      {Result.builder(projectResult)
        .onSuccess((project) => <ProjectHeader title={project.name} />)
        .onInitialOrWaiting(() => (
          <div className="h-14">
            <Skeleton className="w-72 h-7 mt-3 ml-4" />
          </div>
        ))
        .onFailure(() => <ProjectHeader title="Project" />)
        .render()}

      <div className="flex flex-1 flex-col p-4">
        <div className="max-w-5xl mx-auto w-full flex flex-col rounded-lg">
          {/* Prompt input skeleton (same general shape) */}
          {/* <div className="p-4">
            <div className="rounded-lg px-3 py-2">
              <div className="py-2">
                <Skeleton className="h-24 w-full rounded-md" />
              </div>
              <div className="flex justify-end pt-2">
                <Skeleton className="h-9 w-24 rounded-md" />
              </div>
            </div>
          </div> */}

          {/* Chats list */}
          <div className="p-4 pt-0 flex flex-col gap-2">
            <div className="flex items-center justify-between px-3">
              <h3 className="text-xl font-semibold">Chats</h3>

              <Button onClick={handleCreateChat} size="sm">
                <PlusIcon className="size-4" />
                <span>New chat</span>
              </Button>
            </div>

            {Result.builder(chatsResult)
              .onInitialOrWaiting(() => (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  <span>Loading chats…</span>
                </div>
              ))
              .onFailure(() => (
                <div className="text-destructive">Failed to load chats</div>
              ))
              .onSuccess((chats) => (
                <ul className="space-y-2">
                  {chats.map((chat) => (
                    <ChatListItem key={chat.id} chat={chat} />
                  ))}
                </ul>
              ))
              .render()}
          </div>

          <Separator className="mb-6 mx-auto" />

          <div className="p-4 pt-0 flex flex-col gap-2">
            <div className="flex items-center justify-between px-3">
              <h3 className="text-xl font-semibold">Documents</h3>

              <Button onClick={handleCreateDocument} size="sm">
                <PlusIcon className="size-4" />
                <span>New doc</span>
              </Button>
            </div>

            {Result.builder(documentsResult)
              .onInitialOrWaiting(() => (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  <span>Loading documents…</span>
                </div>
              ))
              .onFailure(() => (
                <div className="text-destructive">Failed to load documents</div>
              ))
              .onSuccess((documents) => (
                <ul className="space-y-2">
                  {documents.map((document) => (
                    <DocumentListItem key={document.id} document={document} />
                  ))}
                </ul>
              ))
              .render()}
          </div>

          <Separator className="mb-6 mx-auto" />

          <div className="p-4 pt-0 flex flex-col gap-2">
            <div className="flex items-center justify-between px-3">
              <h3 className="text-xl font-semibold">Materials</h3>

              <Button size="sm" disabled>
                <PlusIcon className="size-4" />
                <span>New material</span>
              </Button>
            </div>

            {Result.builder(materialsResult)
              .onInitialOrWaiting(() => (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  <span>Loading materials…</span>
                </div>
              ))
              .onDefect(() => (
                <div className="text-destructive">Failed to load materials</div>
              ))
              .onSuccess((materials) => (
                <ul className="space-y-2">
                  {materials.map((material) => (
                    <MaterialListItem
                      key={material.data.id}
                      material={material}
                    />
                  ))}
                </ul>
              ))
              .render()}
          </div>
        </div>
      </div>
    </>
  )
}
