import { create } from 'zustand'
import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2Icon } from 'lucide-react'
import { useAtomValue, useAtom } from '@effect-atom/atom-react'
import { indexedDocumentsAtom } from '@/data-acess/document'
import { Result } from '@effect-atom/atom-react'
import type { DocumentDto } from '@/integrations/api/client'
import { createNoteStreamAtom, noteProgressAtom } from '@/data-acess/note'
import { createQuizStreamAtom, quizProgressAtom } from '@/data-acess/quiz'
import {
  createFlashcardGroupStreamAtom,
  flashcardProgressAtom,
} from '@/data-acess/flashcard'
import {
  generateMindMapStreamAtom,
  mindMapProgressAtom,
} from '@/data-acess/mind-map'
import {
  GenerationProgress,
  type ProgressStage,
} from '@/components/generation-progress'

type GenerationDialogStore = {
  isOpen: boolean
  projectId: string | null
  open: (projectId: string) => void
  close: () => void
}

export const useGenerationDialog = create<GenerationDialogStore>((set) => ({
  isOpen: false,
  projectId: null,
  open: (projectId: string) => set({ isOpen: true, projectId }),
  close: () => set({ isOpen: false, projectId: null }),
}))

type GenerationType = 'quiz' | 'flashcard' | 'note' | 'mindmap'
type LengthOption = 'less' | 'normal' | 'more'
type DifficultyOption = 'easy' | 'medium' | 'hard'

export function GenerationDialog() {
  const { isOpen, projectId, close } = useGenerationDialog()
  const [customInstructions, setCustomInstructions] = useState('')
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(
    new Set(),
  )
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedType, setSelectedType] = useState<GenerationType>('note')
  const [length, setLength] = useState<LengthOption>('normal')
  const [difficulty, setDifficulty] = useState<DifficultyOption>('medium')

  const documentsResult = useAtomValue(indexedDocumentsAtom(projectId || ''))

  // Streaming atoms
  const [createNoteStreamResult, createNoteStream] = useAtom(
    createNoteStreamAtom,
    {
      mode: 'promise',
    },
  )
  const [createQuizStreamResult, createQuizStream] = useAtom(
    createQuizStreamAtom,
    {
      mode: 'promise',
    },
  )
  const [createFlashcardStreamResult, createFlashcardStream] = useAtom(
    createFlashcardGroupStreamAtom,
    { mode: 'promise' },
  )
  const [generateMindMapStreamResult, generateMindMapStream] = useAtom(
    generateMindMapStreamAtom,
    { mode: 'promise' },
  )

  // Progress atoms
  const noteProgress = useAtomValue(noteProgressAtom)
  const quizProgress = useAtomValue(quizProgressAtom)
  const flashcardProgress = useAtomValue(flashcardProgressAtom)
  const mindMapProgress = useAtomValue(mindMapProgressAtom)

  // Get current progress based on selected type
  const currentProgress =
    selectedType === 'note'
      ? noteProgress
      : selectedType === 'quiz'
        ? quizProgress
        : selectedType === 'flashcard'
          ? flashcardProgress
          : mindMapProgress

  const handleToggleDocument = (documentId: string) => {
    setSelectedDocumentIds((prev) => {
      const next = new Set(prev)
      if (next.has(documentId)) {
        next.delete(documentId)
      } else {
        next.add(documentId)
      }
      return next
    })
  }

  const handleSelectAll = () => {
    if (!Result.isSuccess(documentsResult)) return

    const allIds = new Set(documentsResult.value.map((doc) => doc.id))
    setSelectedDocumentIds(allIds)
  }

  const handleDeselectAll = () => {
    setSelectedDocumentIds(new Set())
  }

  // Update isGenerating based on streaming state
  useEffect(() => {
    const isStreaming =
      createNoteStreamResult.waiting ||
      createQuizStreamResult.waiting ||
      createFlashcardStreamResult.waiting ||
      generateMindMapStreamResult.waiting

    setIsGenerating(isStreaming)
  }, [
    createNoteStreamResult.waiting,
    createQuizStreamResult.waiting,
    createFlashcardStreamResult.waiting,
    generateMindMapStreamResult.waiting,
  ])

  const handleGenerate = async () => {
    if (!projectId || !customInstructions.trim()) return

    try {
      switch (selectedType) {
        case 'note':
          await createNoteStream({
            projectId,
            customInstructions: customInstructions.trim() || undefined,
            noteId: '',
            count: 30,
            difficulty: difficulty !== 'medium' ? difficulty : undefined,
            topic: customInstructions.trim() || undefined,
          })
          break
        case 'quiz':
          await createQuizStream({
            projectId,
            quizId: '',
            topic: '',
            questionCount: 30,
            customInstructions: customInstructions.trim() || undefined,
            difficulty: difficulty !== 'medium' ? difficulty : undefined,
          })
          break
        case 'flashcard':
          await createFlashcardStream({
            projectId,
            groupId: '',
            flashcardCount: 30,
            customInstructions: customInstructions.trim() || undefined,
            length: length !== 'normal' ? length : undefined,
            difficulty: difficulty !== 'medium' ? difficulty : undefined,
          })
          break
        case 'mindmap':
          await generateMindMapStream({
            projectId,
            customInstructions: customInstructions.trim() || undefined,
          })
          break
      }

      // Close dialog and reset state after a short delay to show completion
      setTimeout(() => {
        handleClose()
      }, 500)
    } catch (error) {
      console.error('Generation failed:', error)
    }
  }

  const handleClose = () => {
    if (isGenerating) return
    close()
    setCustomInstructions('')
    setSelectedDocumentIds(new Set())
    setSelectedType('note')
    setLength('normal')
    setDifficulty('medium')
  }

  const hasSelectedDocuments = selectedDocumentIds.size > 0
  const allDocumentsSelected =
    Result.isSuccess(documentsResult) &&
    documentsResult.value.length > 0 &&
    selectedDocumentIds.size === documentsResult.value.length

  const hasCustomSettings =
    selectedType === 'quiz' ||
    selectedType === 'flashcard' ||
    selectedType === 'note'

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] flex flex-col overflow-hidden">
        <DialogHeader className="shrink-0">
          <DialogTitle>Generate AI Content</DialogTitle>
          <DialogDescription>
            Choose a resource type, enter custom instructions, and select
            relevant documents to generate.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 flex-1 min-h-0 overflow-hidden">
          <div className="space-y-2 shrink-0">
            <Label>Resource Type</Label>
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant={selectedType === 'note' ? 'default' : 'outline'}
                onClick={() => setSelectedType('note')}
                disabled={isGenerating}
              >
                Note
              </Button>
              <Button
                type="button"
                variant={selectedType === 'quiz' ? 'default' : 'outline'}
                onClick={() => setSelectedType('quiz')}
                disabled={isGenerating}
              >
                Quiz
              </Button>
              <Button
                type="button"
                variant={selectedType === 'flashcard' ? 'default' : 'outline'}
                onClick={() => setSelectedType('flashcard')}
                disabled={isGenerating}
              >
                Flashcards
              </Button>
              <Button
                type="button"
                variant={selectedType === 'mindmap' ? 'default' : 'outline'}
                onClick={() => setSelectedType('mindmap')}
                disabled={isGenerating}
              >
                Mind Map
              </Button>
            </div>
          </div>

          <div className="space-y-2 shrink-0">
            <Label htmlFor="customInstructions">Custom Instructions</Label>
            <Textarea
              id="customInstructions"
              placeholder="e.g., Explain the key concepts of machine learning... Format preferences: length (less, normal, more), difficulty (easy, medium, hard)"
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              className="min-h-[100px] resize-none"
              disabled={isGenerating}
            />
          </div>

          {hasCustomSettings && (
            <div className="space-y-3 shrink-0 border rounded-md p-4">
              <Label className="sr-only">Custom Settings</Label>
              <div
                className={`grid gap-4 ${
                  selectedType === 'quiz' || selectedType === 'flashcard'
                    ? 'grid-cols-2'
                    : 'grid-cols-1'
                }`}
              >
                <div className="space-y-2">
                  <Label htmlFor="length">Length</Label>
                  <Select
                    value={length}
                    onValueChange={(value) => setLength(value as LengthOption)}
                    disabled={isGenerating}
                  >
                    <SelectTrigger id="length" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="less">Less</SelectItem>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="more">More</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {(selectedType === 'quiz' || selectedType === 'flashcard') && (
                  <div className="space-y-2">
                    <Label htmlFor="difficulty">Difficulty</Label>
                    <Select
                      value={difficulty}
                      onValueChange={(value) =>
                        setDifficulty(value as DifficultyOption)
                      }
                      disabled={isGenerating}
                    >
                      <SelectTrigger id="difficulty" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="easy">Easy</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="hard">Hard</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="space-y-2 flex-1 min-h-0 flex flex-col">
            <div className="flex items-center justify-between shrink-0">
              <Label>Select Documents</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleSelectAll}
                  disabled={
                    isGenerating ||
                    !Result.isSuccess(documentsResult) ||
                    documentsResult.value.length === 0 ||
                    allDocumentsSelected
                  }
                >
                  Select All
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleDeselectAll}
                  disabled={isGenerating || !hasSelectedDocuments}
                >
                  Deselect All
                </Button>
              </div>
            </div>

            <div className="flex-1 min-h-0 border rounded-md overflow-hidden flex flex-col">
              <div className="flex-1 overflow-y-auto p-4">
                {Result.builder(documentsResult)
                  .onInitialOrWaiting(() => (
                    <div className="flex items-center gap-2 text-muted-foreground py-4">
                      <Loader2Icon className="size-4 animate-spin" />
                      <span>Loading documents…</span>
                    </div>
                  ))
                  .onFailure(() => (
                    <div className="text-destructive py-4">
                      Failed to load documents
                    </div>
                  ))
                  .onSuccess((documents) => {
                    if (documents.length === 0) {
                      return (
                        <div className="text-muted-foreground py-4 text-center">
                          No documents available. Upload documents first.
                        </div>
                      )
                    }

                    return (
                      <div className="space-y-3">
                        {documents.map((document) => (
                          <DocumentCheckbox
                            key={document.id}
                            document={document}
                            checked={selectedDocumentIds.has(document.id)}
                            onCheckedChange={() =>
                              handleToggleDocument(document.id)
                            }
                            disabled={isGenerating}
                          />
                        ))}
                      </div>
                    )
                  })
                  .render()}
              </div>
            </div>
          </div>
        </div>

        {currentProgress && (
          <div className="shrink-0 px-4">
            <GenerationProgress
              status={currentProgress.status as ProgressStage}
              message={currentProgress.message}
              error={currentProgress.error}
            />
          </div>
        )}

        <DialogFooter className="gap-2 shrink-0">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isGenerating}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating || !customInstructions.trim()}
          >
            {isGenerating ? (
              <>
                <Loader2Icon className="size-4 mr-2 animate-spin" />
                Generating{' '}
                {selectedType === 'note'
                  ? 'Note'
                  : selectedType === 'quiz'
                    ? 'Quiz'
                    : selectedType === 'flashcard'
                      ? 'Flashcards'
                      : 'Mind Map'}
                ...
              </>
            ) : (
              `Generate ${
                selectedType === 'note'
                  ? 'Note'
                  : selectedType === 'quiz'
                    ? 'Quiz'
                    : selectedType === 'flashcard'
                      ? 'Flashcards'
                      : 'Mind Map'
              }`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

type DocumentCheckboxProps = {
  document: DocumentDto
  checked: boolean
  onCheckedChange: (checked: boolean) => void
  disabled?: boolean
}

function DocumentCheckbox({
  document,
  checked,
  onCheckedChange,
  disabled,
}: DocumentCheckboxProps) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/50">
      <Checkbox
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
        id={`doc-${document.id}`}
      />
      <Label
        htmlFor={`doc-${document.id}`}
        className="flex-1 cursor-pointer font-normal"
      >
        <div className="flex flex-col">
          <span className="text-sm">{document.file_name}</span>
          <span className="text-xs text-muted-foreground">
            {document.file_type?.toUpperCase()} •{' '}
            {formatFileSize(document.file_size)}
          </span>
        </div>
      </Label>
    </div>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
