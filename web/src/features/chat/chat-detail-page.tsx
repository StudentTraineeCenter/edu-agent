import { chatAtom, streamMessageAtom } from '@/data-acess/chat'
import { Loader2Icon } from 'lucide-react'
import { type PromptInputMessage } from '@/components/ai-elements/prompt-input'
import { useMemo, useRef, useState } from 'react'
import { Result, useAtom, useAtomValue } from '@effect-atom/atom-react'
import { ChatInput } from './components/chat-input'
import { ChatHeader } from './components/chat-header'
import { ChatMessages } from './components/chat-messages'

type ChatContentProps = {
  chatId: string
  projectId: string
}

const ChatContent = ({ chatId, projectId }: ChatContentProps) => {
  const chatResult = useAtomValue(chatAtom(chatId))

  const [prompt, setPrompt] = useState<string>('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [streamMessageResult, streamMessage] = useAtom(streamMessageAtom, {
    mode: 'promise',
  })

  const status = useMemo(() => {
    if (streamMessageResult.waiting) return 'streaming'
    if (streamMessageResult._tag === 'Success') return 'submitted'
    return 'ready'
  }, [streamMessageResult.waiting, streamMessageResult._tag])

  const handleSubmit = async (message: PromptInputMessage) => {
    const value = message.text
    if (!value) return
    setPrompt('')
    try {
      await streamMessage({
        message: value,
        chatId,
      })
    } catch {
      setPrompt(value)
    }
  }

  return Result.builder(chatResult)
    .onInitialOrWaiting(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading chat...</span>
      </div>
    ))
    .onFailure(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
        <span>Failed to load chat</span>
      </div>
    ))
    .onSuccess((chat) => (
      <>
        <div className="flex-1 min-h-0 max-h-full overflow-hidden w-full">
          <ChatMessages messages={chat.messages ?? []} projectId={projectId} />
        </div>
        <div className="shrink-0 bg-background w-full pb-4">
          <div className="max-w-5xl mx-auto">
            <ChatInput
              value={prompt}
              onChange={setPrompt}
              status={status}
              onSubmit={handleSubmit}
              textareaRef={textareaRef}
            />
          </div>
        </div>
      </>
    ))
    .render()
}

type ChatDetailPageProps = {
  projectId: string
  chatId: string
}

export const ChatDetailPage = ({ projectId, chatId }: ChatDetailPageProps) => {
  return (
    <div className="flex h-full flex-col max-h-screen">
      <ChatHeader chatId={chatId} projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 max-h-[calc(100vh-3.5rem)] overflow-hidden w-full">
        <ChatContent chatId={chatId} projectId={projectId} />
      </div>
    </div>
  )
}
