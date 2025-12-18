import { chatAtom } from '@/data-acess/chat'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Loader2Icon } from 'lucide-react'
import { Chatbot } from './chatbot'
import { ChatHeader } from './components/chat-header'

type ChatPageProps = {
  projectId: string
  chatId: string
}

export const ChatPage = ({ projectId, chatId }: ChatPageProps) => {
  const chatKey = `${projectId}:${chatId}`
  const chatResult = useAtomValue(chatAtom(chatKey))

  const isLoading = chatResult.waiting
  const isError = Result.isFailure(chatResult)

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading chat...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
        <span>Failed to load chat</span>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col max-h-screen">
      <ChatHeader chatId={chatId} projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 max-h-[calc(100vh-3.5rem)] overflow-hidden w-full">
        <Chatbot chatId={chatId} projectId={projectId} />
      </div>
    </div>
  )
}
