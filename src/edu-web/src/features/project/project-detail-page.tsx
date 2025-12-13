import { currentProjectIdAtom } from '@/data-acess/project'
import { useNavigate } from '@tanstack/react-router'
import { useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { useEffect } from 'react'
import { chatsAtom, createChatAtom } from '@/data-acess/chat'
import { Button } from '@/components/ui/button'
import { PlusIcon, Loader2Icon } from 'lucide-react'
import { documentsAtom } from '@/data-acess/document'
import { studyResourcesAtom } from '@/data-acess/study-resources'
import { useUploadDocumentDialog } from '@/features/document/components/upload-document-dialog'
import { ProjectHeader } from './components/project-header'
import { ChatListItem } from './components/chat-list-item'
import { DocumentListItem } from './components/document-list-item'
import { StudyResourceListItem } from './components/study-resource-list-item'
import {
  GenerationDialog,
  useGenerationDialog,
} from './components/generation-dialog'
import { Result } from '@effect-atom/atom-react'
import { useDocumentPolling } from '@/hooks/use-document-polling'

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

const AIContentSection = ({ projectId }: { projectId: string }) => {
  const studyResourcesResult = useAtomValue(studyResourcesAtom(projectId))

  return Result.builder(studyResourcesResult)
    .onInitialOrWaiting(() => (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading AI content…</span>
      </div>
    ))
    .onSuccess((studyResources) => (
      <>
        {studyResources.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <p>No AI content yet.</p>
          </div>
        )}

        <ul className="space-y-2">
          {studyResources.map((resource) => (
            <StudyResourceListItem
              key={resource.data.id}
              studyResource={resource}
            />
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
  const openGenerationDialog = useGenerationDialog((state) => state.open)

  const handleCreateChat = async () => {
    const chat = await createChat({ projectId })
    navigate({
      to: '/dashboard/p/$projectId/c/$chatId',
      params: { projectId, chatId: chat.id },
    })
  }

  const handleCreateDocument = () => {
    openUploadDialog(projectId)
  }

  const handleGenerateResource = () => {
    openGenerationDialog(projectId)
  }

  return (
    <div className="flex flex-1 p-4 gap-4 overflow-hidden min-h-0">
      <div className="flex flex-col w-1/2 border rounded-lg p-4 min-h-0">
        <div className="flex items-center justify-between shrink-0 mb-2">
          <h3 className="text-lg font-semibold">Chats</h3>
          <Button onClick={handleCreateChat} size="sm">
            <PlusIcon className="size-4" />
            <span>New chat</span>
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto min-h-0">
          <ChatsSection projectId={projectId} />
        </div>
      </div>

      <div className="flex flex-col w-1/2 gap-4 min-h-0">
        {/* Documents */}
        <div className="flex flex-col border rounded-lg p-4 min-h-0 flex-1">
          <div className="flex items-center justify-between shrink-0 mb-2">
            <h3 className="text-lg font-semibold">Documents</h3>
            <Button onClick={handleCreateDocument} size="sm">
              <PlusIcon className="size-4" />
              <span>Upload</span>
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto min-h-0">
            <DocumentsSection projectId={projectId} />
          </div>
        </div>

        {/* AI Content */}
        <div className="flex flex-col border rounded-lg p-4 min-h-0 flex-1">
          <div className="flex items-center justify-between shrink-0 mb-2">
            <h3 className="text-lg font-semibold">AI Content</h3>
            <Button size="sm" onClick={handleGenerateResource}>
              <PlusIcon className="size-4" />
              <span>Generate</span>
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto min-h-0">
            <AIContentSection projectId={projectId} />
          </div>
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

  // Poll for document status updates when documents are not ready
  useDocumentPolling(projectId)

  return (
    <div className="flex h-full flex-col max-h-screen">
      <ProjectHeader projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 max-h-[calc(100vh-3.5rem)] w-full">
        <ProjectContent projectId={projectId} />
      </div>

      <GenerationDialog />
    </div>
  )
}
