import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation'
import { Loader } from '@/components/ai-elements/loader'
import { Message, MessageContent } from '@/components/ai-elements/message'
import type { PromptInputMessage } from '@/components/ai-elements/prompt-input'
import {
  PromptInput,
  PromptInputActionAddAttachments,
  PromptInputActionMenu,
  PromptInputActionMenuContent,
  PromptInputActionMenuTrigger,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputButton,
  PromptInputFooter,
  PromptInputHeader,
  PromptInputSelect,
  PromptInputSelectContent,
  PromptInputSelectItem,
  PromptInputSelectTrigger,
  PromptInputSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input'
import { Response } from '@/components/ai-elements/response'
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from '@/components/ai-elements/sources'
import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolInput,
  ToolOutput,
} from '@/components/ai-elements/tool'
import {
  chatAtom,
  chatStreamStatusAtom,
  streamMessageAtom,
} from '@/data-acess/chat'
import type {
  ChatMessageDto,
  FilePartDto,
  SourceDocumentPartDto,
  TextPartDto,
  ToolCallPartDto,
} from '@/integrations/api/client'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { CopyIcon, GlobeIcon } from 'lucide-react'
import { useCallback, useState } from 'react'
// Simple ID generator
const generateId = () =>
  `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

const models = [
  {
    name: 'GPT 4o',
    value: 'openai/gpt-4o',
  },
  {
    name: 'Deepseek R1',
    value: 'deepseek/deepseek-r1',
  },
]

interface ChatbotProps {
  chatId: string
  projectId: string
}

export const Chatbot: React.FC<ChatbotProps> = ({ chatId, projectId }) => {
  const [input, setInput] = useState('')
  const [model, setModel] = useState<string>(models[0].value)
  const [webSearch, setWebSearch] = useState(false)

  const chatKey = `${projectId}:${chatId}`
  const chatResult = useAtomValue(chatAtom(chatKey))
  const streamStatus = useAtomValue(chatStreamStatusAtom(chatId))
  const streamMessage = useAtomSet(streamMessageAtom, {
    mode: 'promise',
  })

  const messages = Result.isSuccess(chatResult)
    ? (chatResult.value.messages ?? [])
    : []
  const isStreaming = streamStatus !== null

  // Convert blob URL to data URL
  const blobToDataUrl = useCallback(
    async (blobUrl: string): Promise<string> => {
      const response = await fetch(blobUrl)
      const blob = await response.blob()
      return new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onloadend = () => resolve(reader.result as string)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
    },
    [],
  )

  const handleSubmit = async (message: PromptInputMessage) => {
    const hasText = Boolean(message.text)
    const hasAttachments = Boolean(message.files.length)
    if (!(hasText || hasAttachments)) {
      return
    }

    const parts: (TextPartDto | FilePartDto)[] = []

    // Process text part
    if (hasText) {
      parts.push({
        type: 'text',
        text_content: message.text,
        order: parts.length,
      })
    }

    // Process file attachments - convert to base64 data URLs
    const fileParts = await Promise.all(
      message.files.map(async (file) => {
        // If it's already a URL (from Azure), use it directly
        if (
          file.url &&
          !file.url.startsWith('blob:') &&
          !file.url.startsWith('data:')
        ) {
          return {
            type: 'file' as const,
            file_name: file.filename || 'file',
            file_type: file.mediaType,
            file_url: file.url,
            order: parts.length + message.files.indexOf(file),
          } as FilePartDto
        }

        // Convert blob URL to data URL if needed
        let dataUrl = file.url
        if (file.url?.startsWith('blob:')) {
          dataUrl = await blobToDataUrl(file.url)
        }

        if (!dataUrl || !dataUrl.startsWith('data:')) {
          throw new Error('Invalid file URL')
        }

        // Return file part with base64 data URL
        // The backend will upload it to blob storage and replace with SAS URL
        return {
          type: 'file' as const,
          file_name: file.filename || 'file',
          file_type: file.mediaType,
          file_url: dataUrl, // Base64 data URL - backend will handle upload
          order: parts.length + message.files.indexOf(file),
        } as FilePartDto
      }),
    )

    parts.push(...fileParts)

    // Create user message
    const userMessage: ChatMessageDto = {
      id: generateId(),
      chat_id: chatId,
      role: 'user',
      created_at: new Date().toISOString(),
      parts,
    }

    // Stream the message
    streamMessage({
      message: userMessage,
      projectId: projectId,
      chatId: chatId,
    })

    setInput('')
  }

  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text)
  }, [])

  return (
    <div className="max-w-4xl mx-auto relative size-full h-full">
      <div className="flex flex-col h-full">
        <Conversation className="h-full">
          <ConversationContent>
            {messages.map((message: ChatMessageDto) => (
              <div key={message.id} className="space-y-2">
                {/* Render file attachments for user messages */}
                {message.role === 'user' &&
                  message.parts &&
                  message.parts.filter((part) => part.type === 'file').length >
                    0 && (
                    <Message from="user">
                      <MessageContent>
                        <div className="space-y-2">
                          {message.parts
                            .filter(
                              (part): part is FilePartDto =>
                                part.type === 'file',
                            )
                            .map((part: FilePartDto, i: number) => (
                              <div
                                key={`${message.id}-file-${i}`}
                                className="flex items-center gap-2 p-2 bg-muted rounded"
                              >
                                <span className="text-sm">
                                  {part.file_name}
                                </span>
                                <a
                                  href={part.file_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-primary hover:underline"
                                >
                                  View
                                </a>
                              </div>
                            ))}
                        </div>
                      </MessageContent>
                    </Message>
                  )}

                {/* Collect and render source-document parts together */}
                {message.parts &&
                  (() => {
                    const sourceDocuments = message.parts.filter(
                      (p): p is SourceDocumentPartDto =>
                        p.type === 'source-document',
                    )
                    return sourceDocuments.length > 0 ? (
                      <Sources key={`${message.id}-sources`}>
                        <SourcesTrigger count={sourceDocuments.length} />
                        <SourcesContent>
                          {sourceDocuments.map((sourceDoc, idx) => {
                            // Build URL to view the document
                            // If we have a document_id in provider_metadata, we could link to it
                            // For now, we'll use a placeholder or the source_id
                            const documentUrl = sourceDoc.provider_metadata
                              ?.document_id
                              ? `/dashboard/p/${projectId}/d/${sourceDoc.provider_metadata.document_id}`
                              : `#${sourceDoc.source_id}`

                            return (
                              <Source
                                key={`${message.id}-source-${idx}`}
                                href={documentUrl}
                                title={
                                  sourceDoc.title ||
                                  sourceDoc.filename ||
                                  'Document'
                                }
                              />
                            )
                          })}
                        </SourcesContent>
                      </Sources>
                    ) : null
                  })()}

                {/* Render all parts except source-document (handled above) */}
                {message.parts &&
                  message.parts
                    .filter((part) => part.type !== 'source-document')
                    .map((part, i: number) => {
                      switch (part.type) {
                        case 'text':
                          return (
                            <Message
                              key={`${message.id}-${i}`}
                              from={
                                message.role as 'user' | 'assistant' | 'system'
                              }
                            >
                              <MessageContent>
                                <Response>{part.text_content}</Response>
                              </MessageContent>
                              {message.role === 'assistant' &&
                                i === (message.parts?.length || 0) - 1 && (
                                  <div className="flex gap-2 mt-2">
                                    <button
                                      onClick={() =>
                                        handleCopy(part.text_content)
                                      }
                                      className="p-1 hover:bg-muted rounded"
                                      title="Copy"
                                    >
                                      <CopyIcon className="size-3" />
                                    </button>
                                  </div>
                                )}
                            </Message>
                          )
                        case 'file':
                          // File parts are handled above in the user message section
                          return null
                        // case 'reasoning':
                        //   return (
                        //     <Reasoning
                        //       key={`${message.id}-part-${i}`}
                        //       className="w-full"
                        //       isStreaming={
                        //         isStreaming &&
                        //         i === (message.parts?.length || 0) - 1 &&
                        //         message.id === messages[messages.length - 1]?.id
                        //       }
                        //     >
                        //       <ReasoningTrigger />
                        //       <ReasoningContent>
                        //         {String(
                        //           (
                        //             part as {
                        //               text_content?: string
                        //               text?: string
                        //             }
                        //           ).text_content ||
                        //             (
                        //               part as {
                        //                 text_content?: string
                        //                 text?: string
                        //               }
                        //             ).text ||
                        //             '',
                        //         )}
                        //       </ReasoningContent>
                        //     </Reasoning>
                        //   )
                        case 'tool_call': {
                          const toolCall = part as ToolCallPartDto

                          // Parse tool_output if it's a JSON string
                          let parsedOutput: any = toolCall.tool_output
                          let errorText: string | undefined

                          if (toolCall.tool_state === 'output-error') {
                            errorText =
                              typeof toolCall.tool_output === 'string'
                                ? toolCall.tool_output
                                : JSON.stringify(toolCall.tool_output)
                          } else if (
                            typeof toolCall.tool_output === 'string' &&
                            toolCall.tool_output.trim().startsWith('{')
                          ) {
                            try {
                              parsedOutput = JSON.parse(toolCall.tool_output)
                            } catch {
                              // If parsing fails, use the string as-is
                            }
                          }

                          // Format tool name for display
                          const formatToolName = (name: string) => {
                            return name
                              .split('_')
                              .map(
                                (word) =>
                                  word.charAt(0).toUpperCase() + word.slice(1),
                              )
                              .join(' ')
                          }

                          // Normalize tool_input to object format
                          let normalizedInput: Record<string, any> = {}
                          if (toolCall.tool_input) {
                            if (Array.isArray(toolCall.tool_input)) {
                              normalizedInput = toolCall.tool_input.reduce(
                                (acc, item: any) => {
                                  acc[item.key] = item.value
                                  return acc
                                },
                                {} as Record<string, any>,
                              )
                            } else {
                              normalizedInput = toolCall.tool_input as Record<
                                string,
                                any
                              >
                            }
                          }

                          // Map tool_state to ToolUIPart state format
                          // Map to valid states, defaulting to 'input-available' for unknown states
                          const stateMap: Record<
                            string,
                            | 'input-streaming'
                            | 'input-available'
                            | 'output-available'
                            | 'output-error'
                          > = {
                            'input-streaming': 'input-streaming',
                            'input-available': 'input-available',
                            'output-available': 'output-available',
                            'output-error': 'output-error',
                          }
                          const toolState =
                            stateMap[toolCall.tool_state] || 'input-available'

                          return (
                            <Tool
                              key={`${message.id}-part-${i}`}
                              defaultOpen={
                                toolCall.tool_state === 'output-error'
                              }
                            >
                              <ToolHeader
                                title={formatToolName(toolCall.tool_name)}
                                type={`tool-${toolCall.tool_name}`}
                                state={toolState}
                              />
                              <ToolContent>
                                {Object.keys(normalizedInput).length > 0 && (
                                  <ToolInput input={normalizedInput} />
                                )}
                                {(parsedOutput || errorText) && (
                                  <ToolOutput
                                    output={parsedOutput}
                                    errorText={errorText}
                                  />
                                )}
                              </ToolContent>
                            </Tool>
                          )
                        }
                        // case 'source-url':
                        //   return (
                        //     <div
                        //       key={`${message.id}-part-${i}`}
                        //       className="bg-card text-card-foreground p-3 rounded-lg border-l-4 border-primary ring-1 ring-foreground/10"
                        //     >
                        //       <span className="text-xs text-muted-foreground font-medium">
                        //         Source URL:
                        //       </span>
                        //       <a
                        //         href={(part as { url?: string }).url}
                        //         target="_blank"
                        //         rel="noopener noreferrer"
                        //         className="block text-primary hover:text-primary/80 underline text-sm mt-1 underline-offset-4"
                        //       >
                        //         {(part as { url?: string }).url}
                        //       </a>
                        //     </div>
                        //   )
                        // source-document parts are handled above in the Sources component
                        default:
                          return null
                      }
                    })}
              </div>
            ))}
            {isStreaming && <Loader />}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <PromptInput
          onSubmit={handleSubmit}
          className="mt-4"
          globalDrop
          multiple
        >
          <PromptInputHeader>
            <PromptInputAttachments>
              {(attachment) => <PromptInputAttachment data={attachment} />}
            </PromptInputAttachments>
          </PromptInputHeader>
          <PromptInputBody>
            <PromptInputTextarea
              onChange={(e) => setInput(e.target.value)}
              value={input}
            />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools>
              <PromptInputActionMenu>
                <PromptInputActionMenuTrigger />
                <PromptInputActionMenuContent>
                  <PromptInputActionAddAttachments />
                </PromptInputActionMenuContent>
              </PromptInputActionMenu>
              <PromptInputButton
                variant={webSearch ? 'default' : 'ghost'}
                onClick={() => setWebSearch(!webSearch)}
              >
                <GlobeIcon size={16} />
                <span>Search</span>
              </PromptInputButton>
              <PromptInputSelect
                onValueChange={(value) => {
                  setModel(value as string)
                }}
                value={model}
              >
                <PromptInputSelectTrigger>
                  <PromptInputSelectValue />
                </PromptInputSelectTrigger>
                <PromptInputSelectContent>
                  {models.map((item) => (
                    <PromptInputSelectItem key={item.value} value={item.value}>
                      {item.name}
                    </PromptInputSelectItem>
                  ))}
                </PromptInputSelectContent>
              </PromptInputSelect>
            </PromptInputTools>
            <PromptInputSubmit
              disabled={!input && !isStreaming}
              status={isStreaming ? 'streaming' : 'ready'}
            />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  )
}
