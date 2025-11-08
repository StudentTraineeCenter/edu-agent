import { currentProjectIdAtom } from '@/data-acess/project'
import { useNavigate } from '@tanstack/react-router'
import { useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { useEffect } from 'react'
import { chatsAtom, createChatAtom } from '@/data-acess/chat'
import { Button } from '@/components/ui/button'
import { PlusIcon, Loader2Icon } from 'lucide-react'
import { documentsAtom } from '@/data-acess/document'
import { materialsAtom } from '@/data-acess/materials'
import { useUploadDocumentDialog } from '@/features/document/components/upload-document-dialog'
import { Separator } from '@/components/ui/separator'
import { ProjectHeader } from './components/project-header'
import { ChatListItem } from './components/chat-list-item'
import { DocumentListItem } from './components/document-list-item'
import { MaterialListItem } from './components/material-list-item'
import { Result } from '@effect-atom/atom-react'

const ChatsSection = ({ projectId }: { projectId: string }) => {
  const chatsResult = useAtomValue(chatsAtom(projectId))

  return Result.builder(chatsResult)
    .onInitialOrWaiting(() => (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading chats…</span>
      </div>
    ))
    .onFailure(() => (
      <div className="text-destructive">Failed to load chats</div>
    ))
    .onSuccess((chats) => (
      <>
        {chats.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <p>No chats yet. Create your first chat to get started.</p>
          </div>
        )}

        <ul className="space-y-2">
          {chats.map((chat) => (
            <ChatListItem key={chat.id} chat={chat} />
          ))}
        </ul>
      </>
    ))
    .render()
}

const DocumentsSection = ({ projectId }: { projectId: string }) => {
  const documentsResult = useAtomValue(documentsAtom(projectId))

  return Result.builder(documentsResult)
    .onInitialOrWaiting(() => (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading documents…</span>
      </div>
    ))
    .onFailure(() => (
      <div className="text-destructive">Failed to load documents</div>
    ))
    .onSuccess((documents) => (
      <>
        {documents.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <p>No documents yet. Upload your first document to get started.</p>
          </div>
        )}

        <ul className="space-y-2">
          {documents.map((document) => (
            <DocumentListItem key={document.id} document={document} />
          ))}
        </ul>
      </>
    ))
    .render()
}

const MaterialsSection = ({ projectId }: { projectId: string }) => {
  const materialsResult = useAtomValue(materialsAtom(projectId))

  return Result.builder(materialsResult)
    .onInitialOrWaiting(() => (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading materials…</span>
      </div>
    ))
    .onSuccess((materials) => (
      <>
        {materials.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <p>No materials yet.</p>
          </div>
        )}

        <ul className="space-y-2">
          {materials.map((material) => (
            <MaterialListItem key={material.data.id} material={material} />
          ))}
        </ul>
      </>
    ))
    .render()
}

type ProjectContentProps = {
  projectId: string
}

const ProjectContent = ({ projectId }: ProjectContentProps) => {
  const navigate = useNavigate()

  const createChat = useAtomSet(createChatAtom, {
    mode: 'promise',
  })
  const openUploadDialog = useUploadDocumentDialog((state) => state.open)

  const handleCreateChat = async () => {
    const chat = await createChat({ project_id: projectId })
    navigate({
      to: '/p/$projectId/c/$chatId',
      params: { projectId, chatId: chat.id },
    })
  }

  const handleCreateDocument = () => {
    openUploadDialog(projectId)
  }

  return (
    <div className="flex flex-1 flex-col p-4">
      <div className="max-w-5xl mx-auto w-full flex flex-col rounded-lg">
        {/* Chats list */}
        <div className="p-4 pt-0 flex flex-col gap-2">
          <div className="flex items-center justify-between px-3">
            <h3 className="text-xl font-semibold">Chats</h3>

            <Button onClick={handleCreateChat} size="sm">
              <PlusIcon className="size-4" />
              <span>New chat</span>
            </Button>
          </div>

          <ChatsSection projectId={projectId} />
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

          <DocumentsSection projectId={projectId} />
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

          <MaterialsSection projectId={projectId} />
        </div>
      </div>
    </div>
  )
}

type ProjectDetailPageProps = {
  projectId: string
}

export const ProjectDetailPage = ({ projectId }: ProjectDetailPageProps) => {
  const setCurrentProject = useAtomSet(currentProjectIdAtom)

  useEffect(() => {
    setCurrentProject(projectId)
  }, [projectId, setCurrentProject])

  return (
    <div className="flex h-full flex-col max-h-screen">
      <ProjectHeader projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 max-h-[calc(100vh-3.5rem)] overflow-hidden w-full">
        <ProjectContent projectId={projectId} />
      </div>
    </div>
  )
}
