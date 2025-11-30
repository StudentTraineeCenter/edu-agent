import { create } from 'zustand'
import { useState } from 'react'
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
import { Loader2Icon } from 'lucide-react'
import { useAtomValue } from '@effect-atom/atom-react'
import { indexedDocumentsAtom } from '@/data-acess/document'
import { Result } from '@effect-atom/atom-react'
import type { DocumentDto } from '@/integrations/api/client'

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

type GenerationType = 'quiz' | 'flashcard'

export function GenerationDialog() {
  const { isOpen, projectId, close } = useGenerationDialog()
  const [prompt, setPrompt] = useState('')
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(
    new Set(),
  )
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationType, setGenerationType] = useState<GenerationType | null>(
    null,
  )

  const documentsResult = useAtomValue(indexedDocumentsAtom(projectId || ''))

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

  const handleGenerate = async (type: GenerationType) => {
    if (!projectId || !prompt.trim()) return

    setIsGenerating(true)
    setGenerationType(type)

    try {
      // TODO: Implement actual generation logic
      // For now, this is a placeholder
      console.log('Generating', type, {
        projectId,
        prompt,
        documentIds: Array.from(selectedDocumentIds),
      })

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Close dialog and reset state
      handleClose()
    } catch (error) {
      console.error('Generation failed:', error)
    } finally {
      setIsGenerating(false)
      setGenerationType(null)
    }
  }

  const handleClose = () => {
    if (isGenerating) return
    close()
    setPrompt('')
    setSelectedDocumentIds(new Set())
    setGenerationType(null)
  }

  const hasSelectedDocuments = selectedDocumentIds.size > 0
  const allDocumentsSelected =
    Result.isSuccess(documentsResult) &&
    documentsResult.value.length > 0 &&
    selectedDocumentIds.size === documentsResult.value.length

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] flex flex-col overflow-hidden">
        <DialogHeader className="shrink-0">
          <DialogTitle>Generate Study Resource</DialogTitle>
          <DialogDescription>
            Enter a topic or prompt and select relevant documents to generate a
            quiz or flashcard set.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 flex-1 min-h-0 overflow-hidden">
          <div className="space-y-2 shrink-0">
            <Label htmlFor="prompt">Topic / Prompt</Label>
            <Textarea
              id="prompt"
              placeholder="e.g., Explain the key concepts of machine learning..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-[100px] resize-none"
              disabled={isGenerating}
            />
          </div>

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
            onClick={() => handleGenerate('quiz')}
            disabled={isGenerating || !prompt.trim()}
          >
            {isGenerating && generationType === 'quiz' ? (
              <>
                <Loader2Icon className="size-4 mr-2 animate-spin" />
                Generating Quiz...
              </>
            ) : (
              'Generate Quiz'
            )}
          </Button>
          <Button
            type="button"
            onClick={() => handleGenerate('flashcard')}
            disabled={isGenerating || !prompt.trim()}
          >
            {isGenerating && generationType === 'flashcard' ? (
              <>
                <Loader2Icon className="size-4 mr-2 animate-spin" />
                Generating Flashcards...
              </>
            ) : (
              'Generate Flashcards'
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
