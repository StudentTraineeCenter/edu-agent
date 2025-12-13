import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  ArrowUpIcon,
  ArrowDownIcon,
  TrashIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from 'lucide-react'
import { cn, truncate } from '@/lib/utils'

type FlashcardEditorProps = {
  flashcard: {
    id: string
    question: string
    answer: string
    difficulty_level: string
    position: number
  }
  onQuestionChange: (value: string) => void
  onAnswerChange: (value: string) => void
  onDifficultyChange: (value: string) => void
  onDelete: () => void
  onMoveUp: () => void
  onMoveDown: () => void
  canMoveUp: boolean
  canMoveDown: boolean
  isDeleted?: boolean
}

export const FlashcardEditor = ({
  flashcard,
  onQuestionChange,
  onAnswerChange,
  onDifficultyChange,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  isDeleted = false,
}: FlashcardEditorProps) => {
  const [isOpen, setIsOpen] = useState(false)

  if (isDeleted) {
    return (
      <Card className="opacity-50 border-dashed">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Card #{flashcard.position + 1} (deleted)
              </span>
            </div>
          </div>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="hover:shadow-md transition-shadow gap-0">
        <CollapsibleTrigger asChild>
          <CardHeader className="pt-2 cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {isOpen ? (
                  <ChevronUpIcon className="h-4 w-4 text-muted-foreground shrink-0" />
                ) : (
                  <ChevronDownIcon className="h-4 w-4 text-muted-foreground shrink-0" />
                )}
                <span className="text-sm text-muted-foreground shrink-0">
                  Card #{flashcard.position + 1}
                </span>
                {!isOpen && flashcard.question && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-sm text-foreground truncate ml-2 block">
                        {truncate(flashcard.question, 120)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent
                      side="bottom"
                      align="start"
                      className="max-w-md"
                    >
                      <p className="whitespace-normal break-words">
                        {flashcard.question}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
              <div
                className="flex items-center gap-2 shrink-0"
                onClick={(e) => e.stopPropagation()}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onMoveUp}
                  disabled={!canMoveUp}
                  title="Move up"
                >
                  <ArrowUpIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onMoveDown}
                  disabled={!canMoveDown}
                  title="Move down"
                >
                  <ArrowDownIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDelete}
                  title="Delete"
                >
                  <TrashIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent
          className={cn(
            'overflow-hidden',
            'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:slide-out-to-top-2',
            'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-top-2',
            'transition-all duration-300 ease-in-out',
          )}
        >
          <CardContent className="space-y-4 pt-0">
            <div className="space-y-2">
              <label className="text-sm font-medium">Question</label>
              <Textarea
                value={flashcard.question}
                onChange={(e) => onQuestionChange(e.target.value)}
                placeholder="Enter question..."
                className="min-h-20"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Answer</label>
              <Textarea
                value={flashcard.answer}
                onChange={(e) => onAnswerChange(e.target.value)}
                placeholder="Enter answer..."
                className="min-h-20"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Difficulty</label>
              <Select
                value={flashcard.difficulty_level}
                onValueChange={onDifficultyChange}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
