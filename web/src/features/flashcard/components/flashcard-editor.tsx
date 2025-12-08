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
import { ArrowUpIcon, ArrowDownIcon, TrashIcon } from 'lucide-react'

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
    <Card className="hover:shadow-md transition-shadow gap-0">
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Card #{flashcard.position + 1}
            </span>
          </div>
          <div className="flex items-center gap-2">
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
            <Button variant="ghost" size="sm" onClick={onDelete} title="Delete">
              <TrashIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
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
    </Card>
  )
}
