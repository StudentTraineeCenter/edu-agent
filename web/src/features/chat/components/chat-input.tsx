import {
  type PromptInputMessage,
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputSubmit,
} from '@/components/ai-elements/prompt-input'
import React from 'react'

type Props = {
  value: string
  onChange: (value: string) => void
  status: 'streaming' | 'error' | 'ready' | 'submitted'
  onSubmit: (message: PromptInputMessage) => void
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
}

export const ChatInput: React.FC<Props> = ({
  value,
  onChange,
  status,
  onSubmit,
  textareaRef,
}) => (
  <PromptInput multiple onSubmit={onSubmit}>
    <PromptInputBody>
      <PromptInputTextarea
        onChange={(e) => onChange(e.target.value)}
        ref={textareaRef}
        value={value}
      />
    </PromptInputBody>
    <PromptInputToolbar className="justify-end">
      <PromptInputSubmit status={status} />
    </PromptInputToolbar>
  </PromptInput>
)
