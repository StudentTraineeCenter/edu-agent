import { useNavigate } from '@tanstack/react-router'
import {
  Message,
  MessageAvatar,
  MessageContent,
} from '@/components/ai-elements/message'
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation'
import { MessageSquareIcon, Loader2Icon } from 'lucide-react'
import { Response } from '@/components/ai-elements/response'
import {
  Sources,
  SourcesTrigger,
  SourcesContent,
  Source,
} from '@/components/ai-elements/sources'
import {
  Tool,
  ToolHeader,
  ToolContent,
  ToolInput,
  ToolOutput,
} from '@/components/ai-elements/tool'
import type {
  ChatMessageDto,
  SourceDto,
  ToolCallDto,
} from '@/integrations/api/client'
import { chatStreamStatusAtom } from '@/data-acess/chat'
import { useAtomValue } from '@effect-atom/atom-react'

type Props = {
  messages: ReadonlyArray<ChatMessageDto>
  projectId: string
  chatId: string
  isStreaming?: boolean
  hasAssistantResponse?: boolean
}

type MessageToolsProps = {
  tools: ReadonlyArray<ToolCallDto>
}

const MessageTools = ({ tools }: MessageToolsProps) => {
  if (!tools || tools.length === 0) return null

  return (
    <div className="space-y-2">
      {tools.map((tool) => {
        const hasOutput = tool.output || tool.error_text
        return (
          <Tool key={tool.id}>
            <ToolHeader
              title={tool.name}
              type={`tool-${tool.type}`}
              state={tool.state}
            />
            <ToolContent>
              {tool.input && <ToolInput input={tool.input} />}
              {hasOutput && (
                <ToolOutput
                  output={tool.output}
                  errorText={tool.error_text ?? undefined}
                />
              )}
            </ToolContent>
          </Tool>
        )
      })}
    </div>
  )
}

type MessageSourcesProps = {
  sources: ReadonlyArray<SourceDto>
  projectId: string
}

const MessageSources = ({ sources, projectId }: MessageSourcesProps) => {
  const navigate = useNavigate()

  const handleSourceClick = (source: SourceDto) => {
    if (!source.document_id) return
    navigate({
      to: '/dashboard/p/$projectId/d/$documentId',
      params: {
        projectId,
        documentId: source.document_id,
      },
    })
  }

  if (!sources || sources.length === 0) return null

  return (
    <Sources>
      <SourcesTrigger count={sources.length} />
      <SourcesContent>
        {sources.map((source) => (
          <Source
            key={source.id}
            href="#"
            onClick={() => handleSourceClick(source)}
            title={`[${source.citation_index}] ${source.title}`}
          />
        ))}
      </SourcesContent>
    </Sources>
  )
}

type UserMessageProps = {
  message: ChatMessageDto
  photoUrl?: string
}

const UserMessage = ({ message, photoUrl }: UserMessageProps) => (
  <Message from="user">
    <MessageContent>{message.content}</MessageContent>
    <MessageAvatar name="User" src={photoUrl ?? ''} />
  </Message>
)

type AssistantMessageProps = {
  message: ChatMessageDto
  projectId: string
}

const AssistantMessage = ({ message, projectId }: AssistantMessageProps) => {
  const hasContent = message.content && message.content.trim().length > 0
  const hasTools = message.tools && message.tools.length > 0
  const hasSources = message.sources && message.sources.length > 0

  // Don't render empty assistant messages
  if (!hasContent && !hasTools && !hasSources) return null

  return (
    <Message from="assistant">
      <MessageContent>
        <MessageTools tools={message.tools ?? []} />
        <Response>{message.content}</Response>
        <MessageSources sources={message.sources ?? []} projectId={projectId} />
      </MessageContent>
      <MessageAvatar name="AI" src="https://github.com/openai.png" />
    </Message>
  )
}

type ChatMessageItemProps = {
  message: ChatMessageDto
  projectId: string
}

const ChatMessageItem = ({ message, projectId }: ChatMessageItemProps) => {
  if (message.role === 'user') {
    return <UserMessage message={message} />
  }
  return <AssistantMessage message={message} projectId={projectId} />
}

const getStatusMessage = (status: string | null): string => {
  if (!status) return 'EduAgent is thinking...'

  const statusMessages: Record<string, string> = {
    thinking: 'EduAgent is thinking...',
    searching: 'EduAgent is searching documents...',
    generating: 'EduAgent is generating response...',
  }

  return statusMessages[status] || 'EduAgent is thinking...'
}

type ThinkingMessageProps = {
  chatId: string
}

const ThinkingMessage = ({ chatId }: ThinkingMessageProps) => {
  const streamStatus = useAtomValue(chatStreamStatusAtom(chatId))
  const statusMessage = getStatusMessage(streamStatus)

  return (
    <Message from="assistant">
      <MessageContent>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2Icon className="size-4 animate-spin" />
          <span>{statusMessage}</span>
        </div>
      </MessageContent>
      <MessageAvatar name="AI" src="https://github.com/openai.png" />
    </Message>
  )
}

export const ChatMessages = ({
  messages,
  projectId,
  chatId,
  isStreaming,
  hasAssistantResponse,
}: Props) => {
  const showThinkingIndicator = isStreaming && !hasAssistantResponse

  return (
    <Conversation className="flex-1 min-h-0 max-h-full w-full">
      <ConversationContent className="max-w-5xl mx-auto">
        {messages.length === 0 && !showThinkingIndicator && (
          <ConversationEmptyState
            icon={<MessageSquareIcon className="size-6" />}
            title="Start a conversation"
            description="Messages will appear here as the conversation progresses."
          />
        )}

        {messages.map((msg, index) => (
          <ChatMessageItem
            key={msg.id ?? index}
            message={msg}
            projectId={projectId}
          />
        ))}

        {showThinkingIndicator && <ThinkingMessage chatId={chatId} />}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  )
}
