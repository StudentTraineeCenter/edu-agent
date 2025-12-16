import { Loader2Icon } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { Result, useAtom, useAtomValue } from '@effect-atom/atom-react'
import { ChatInput } from './components/chat-input'
import { ChatHeader } from './components/chat-header'
import { ChatMessages } from './components/chat-messages'
import type { PromptInputMessage } from '@/components/ai-elements/prompt-input'
import { chatAtom, streamMessageAtom } from '@/data-acess/chat'
import { Suggestion, Suggestions } from '@/components/ai-elements/suggestion'

type ChatContentProps = {
  chatId: string
  projectId: string
}

const ChatContent = ({ chatId, projectId }: ChatContentProps) => {
  const atomInput = useMemo(() => `${projectId}:${chatId}`, [projectId, chatId])
  const chatResult = useAtomValue(chatAtom(atomInput))

  const [prompt, setPrompt] = useState<string>('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [streamMessageResult, streamMessage] = useAtom(streamMessageAtom, {
    mode: 'promise',
  })

  // Check if there's an assistant response with content (not just streaming)
  const hasAssistantResponse = useMemo(() => {
    if (!Result.isSuccess(chatResult)) return false
    const messages = chatResult.value.messages ?? []
    const lastMessage = messages[messages.length - 1]
    return (
      lastMessage?.role === 'assistant' &&
      !!lastMessage.content &&
      lastMessage.content.trim().length > 0
    )
  }, [chatResult])

  const status = useMemo(() => {
    // Show loading on button only until first response chunk arrives
    if (streamMessageResult.waiting && !hasAssistantResponse) return 'submitted'
    return 'ready'
  }, [streamMessageResult.waiting, hasAssistantResponse])

  const handleSubmit = async (message: PromptInputMessage) => {
    const value = message.text
    if (!value) return
    setPrompt('')
    try {
      await streamMessage({
        message: value,
        projectId,
        chatId,
      })
    } catch {
      setPrompt(value)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setPrompt(suggestion)
    textareaRef.current?.focus()
  }

  const suggestions = [
    'What are the latest trends in AI?',
    'How does machine learning work?',
    'Explain quantum computing',
    'Best practices for React development',
    'Tell me about TypeScript benefits',
    'How to optimize database queries?',
    'What is the difference between SQL and NoSQL?',
    'Explain cloud computing basics',
  ]

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
          <ChatMessages
            messages={chat.messages ?? []}
            projectId={projectId}
            chatId={chatId}
            isStreaming={streamMessageResult.waiting}
            hasAssistantResponse={hasAssistantResponse}
          />
        </div>
        <div className="shrink-0 bg-background w-full pb-4">
          <div className="max-w-5xl mx-auto">
            <div className="grid shrink-0 gap-4 pt-4">
              <Suggestions className="px-4">
                {suggestions.map((suggestion) => (
                  <Suggestion
                    key={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    suggestion={suggestion}
                  />
                ))}
              </Suggestions>
              <div className="w-full px-4 pb-4">
                <ChatInput
                  value={prompt}
                  onChange={setPrompt}
                  status={status}
                  onSubmit={handleSubmit}
                  textareaRef={textareaRef}
                />
              </div>
            </div>
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
