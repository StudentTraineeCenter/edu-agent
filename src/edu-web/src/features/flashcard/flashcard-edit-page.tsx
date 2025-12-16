import {
  Result,
  useAtom,
  useAtomSet,
  useAtomValue,
} from '@effect-atom/atom-react'
import { Link } from '@tanstack/react-router'
import { ArrowLeft, PlusIcon, SaveIcon } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { FlashcardEditor } from './components/flashcard-editor'
import {
  createFlashcardAtom,
  deleteFlashcardAtom,
  flashcardGroupAtom,
  flashcardsAtom,
  reorderFlashcardsAtom,
  updateFlashcardAtom,
} from '@/data-acess/flashcard'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

type FlashcardEditPageProps = {
  flashcardGroupId: string
  projectId: string
}

type LocalFlashcard = {
  id: string
  question: string
  answer: string
  difficulty_level: string
  position: number
  isNew?: boolean
  isDeleted?: boolean
  originalId?: string // For new cards that need to be created
}

const FlashcardHeaderContent = ({
  flashcardGroupId,
  projectId,
}: {
  projectId: string
  flashcardGroupId: string
}) => {
  const flashcardGroupKey = useMemo(
    () => `${projectId}:${flashcardGroupId}`,
    [projectId, flashcardGroupId],
  )
  const groupResult = useAtomValue(flashcardGroupAtom(flashcardGroupKey))

  return Result.builder(groupResult)
    .onSuccess((res) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              Edit: {res.name || 'Flashcards'}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .onFailure(() => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              Edit Flashcards
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

export const FlashcardEditPage = ({
  flashcardGroupId,
  projectId,
}: FlashcardEditPageProps) => {
  const flashcardGroupKey = useMemo(
    () => `${projectId}:${flashcardGroupId}`,
    [projectId, flashcardGroupId],
  )
  const flashcardsResult = useAtomValue(flashcardsAtom(flashcardGroupKey))
  const groupResult = useAtomValue(flashcardGroupAtom(flashcardGroupKey))
  const [createFlashcardResult, createFlashcard] = useAtom(
    createFlashcardAtom,
    { mode: 'promise' },
  )
  const [updateFlashcardResult, updateFlashcard] = useAtom(
    updateFlashcardAtom,
    { mode: 'promise' },
  )
  const reorderFlashcards = useAtomSet(reorderFlashcardsAtom, {
    mode: 'promise',
  })
  const deleteFlashcard = useAtomSet(deleteFlashcardAtom, {
    mode: 'promise',
  })

  // Local state for all flashcards
  const [localFlashcards, setLocalFlashcards] = useState<Array<LocalFlashcard>>(
    [],
  )
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [newQuestion, setNewQuestion] = useState('')
  const [newAnswer, setNewAnswer] = useState('')
  const [newDifficulty, setNewDifficulty] = useState('medium')
  const [nextTempId, setNextTempId] = useState(1)

  // Initialize local flashcards from server data
  useEffect(() => {
    if (Result.isSuccess(flashcardsResult)) {
      const flashcards = flashcardsResult.value
      setLocalFlashcards(
        flashcards.map((f) => ({
          id: f.id,
          question: f.question,
          answer: f.answer,
          difficulty_level: f.difficulty_level,
          position: f.position,
        })),
      )
    }
  }, [flashcardsResult])

  // Check if there are unsaved changes
  const hasUnsavedChanges = useMemo(() => {
    if (!Result.isSuccess(flashcardsResult)) return false

    const original = flashcardsResult.value
    const current = localFlashcards.filter((f) => !f.isDeleted)

    // Check for new cards
    const hasNew = localFlashcards.some((f) => f.isNew)

    // Check for deleted cards
    const hasDeleted = localFlashcards.some((f) => f.isDeleted)

    // Check for modified cards
    const hasModified = original.some((orig) => {
      const local = localFlashcards.find(
        (l) => l.id === orig.id && !l.isDeleted,
      )
      if (!local) return false
      return (
        local.question !== orig.question ||
        local.answer !== orig.answer ||
        local.difficulty_level !== orig.difficulty_level
      )
    })

    // Check for reordered cards
    const originalIds = original.map((f) => f.id)
    const currentIds = current.map((f) => f.id)
    const hasReordered =
      JSON.stringify(originalIds) !== JSON.stringify(currentIds)

    return hasNew || hasDeleted || hasModified || hasReordered
  }, [flashcardsResult, localFlashcards])

  const handleAddCard = () => {
    if (!newQuestion.trim() || !newAnswer.trim()) return

    const newCard: LocalFlashcard = {
      id: `temp-${nextTempId}`,
      question: newQuestion,
      answer: newAnswer,
      difficulty_level: newDifficulty,
      position: localFlashcards.length,
      isNew: true,
      originalId: `temp-${nextTempId}`,
    }

    setLocalFlashcards((prev) => [...prev, newCard])
    setNextTempId((prev) => prev + 1)
    setNewQuestion('')
    setNewAnswer('')
    setNewDifficulty('medium')
    setIsAddDialogOpen(false)
  }

  const handleDelete = useCallback((index: number) => {
    setLocalFlashcards((prev) => {
      const updated = [...prev]
      const card = updated[index]
      if (card.isNew) {
        // Remove new cards completely
        updated.splice(index, 1)
      } else {
        // Mark existing cards as deleted
        updated[index] = { ...card, isDeleted: true }
      }
      return updated
    })
  }, [])

  const handleMoveUp = useCallback((index: number) => {
    if (index === 0) return
    setLocalFlashcards((prev) => {
      const updated = [...prev]
      ;[updated[index - 1], updated[index]] = [
        updated[index],
        updated[index - 1],
      ]
      // Update positions
      return updated.map((card, idx) => ({ ...card, position: idx }))
    })
  }, [])

  const handleMoveDown = useCallback((index: number) => {
    setLocalFlashcards((prev) => {
      if (index >= prev.length - 1) return prev
      const updated = [...prev]
      ;[updated[index], updated[index + 1]] = [
        updated[index + 1],
        updated[index],
      ]
      // Update positions
      return updated.map((card, idx) => ({ ...card, position: idx }))
    })
  }, [])

  const handleUpdateCard = useCallback(
    (
      index: number,
      field: 'question' | 'answer' | 'difficulty_level',
      value: string,
    ) => {
      setLocalFlashcards((prev) => {
        const updated = [...prev]
        updated[index] = { ...updated[index], [field]: value }
        return updated
      })
    },
    [],
  )

  const handleSave = async () => {
    if (!hasUnsavedChanges) return

    const activeCards = localFlashcards.filter((f) => !f.isDeleted)
    const original = Result.isSuccess(flashcardsResult)
      ? flashcardsResult.value
      : []

    try {
      // 1. Delete removed cards
      const toDelete = original.filter(
        (orig) => !activeCards.find((active) => active.id === orig.id),
      )
      for (const card of toDelete) {
        await deleteFlashcard({
          flashcardId: card.id,
          projectId,
          flashcardGroupId,
        })
      }

      // 2. Create new cards
      const toCreate = activeCards.filter((card) => card.isNew)
      for (const card of toCreate) {
        await createFlashcard({
          projectId,
          flashcardGroupId,
          question: card.question,
          answer: card.answer,
          difficultyLevel: card.difficulty_level,
          position: card.position,
        })
      }

      // 3. Update modified cards
      const toUpdate = activeCards.filter((card) => {
        if (card.isNew) return false
        const orig = original.find((o) => o.id === card.id)
        if (!orig) return false
        return (
          card.question !== orig.question ||
          card.answer !== orig.answer ||
          card.difficulty_level !== orig.difficulty_level
        )
      })
      for (const card of toUpdate) {
        await updateFlashcard({
          flashcardId: card.id,
          projectId,
          flashcardGroupId,
          question: card.question,
          answer: card.answer,
          difficultyLevel: card.difficulty_level,
        })
      }

      // 4. Reorder if needed
      const originalIds = original.map((f) => f.id)
      const currentIds = activeCards.filter((c) => !c.isNew).map((c) => c.id)
      const hasReordered =
        JSON.stringify(originalIds) !== JSON.stringify(currentIds)

      if (hasReordered) {
        await reorderFlashcards({
          projectId,
          flashcardGroupId,
          flashcardIds: activeCards.filter((c) => !c.isNew).map((c) => c.id),
        })
      }
    } catch (error) {
      console.error('Failed to save changes:', error)
    }
  }

  const visibleCards = localFlashcards.filter((f) => !f.isDeleted)

  return (
    <div className="flex h-full flex-col">
      <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2 z-10">
        <div className="flex flex-1 items-center gap-2 px-3">
          {Result.isSuccess(groupResult) && (
            <>
              <SidebarTrigger />
              <Button variant="ghost" size="icon" className="size-7" asChild>
                <Link
                  to="/dashboard/p/$projectId/f/$flashcardGroupId"
                  params={{ projectId, flashcardGroupId }}
                >
                  <ArrowLeft className="size-4" />
                  <span className="sr-only">Back to flashcards</span>
                </Link>
              </Button>
            </>
          )}
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <FlashcardHeaderContent
            projectId={projectId}
            flashcardGroupId={flashcardGroupId}
          />
        </div>
        <div className="flex items-center gap-2 px-3">
          {hasUnsavedChanges && (
            <span className="text-sm text-muted-foreground">
              Unsaved changes
            </span>
          )}
          <Button
            onClick={handleSave}
            disabled={
              !hasUnsavedChanges ||
              updateFlashcardResult.waiting ||
              createFlashcardResult.waiting
            }
          >
            <SaveIcon className="h-4 w-4 mr-2" />
            Save All
          </Button>
        </div>
      </header>

      <div className="flex flex-1 flex-col min-h-0 overflow-auto">
        <div className="min-h-screen bg-background p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">
                  Edit Flashcards
                </h1>
                <p className="text-muted-foreground mt-2">
                  Add, edit, and reorder your flashcards. Click "Save All" when
                  done.
                </p>
              </div>
              <Button onClick={() => setIsAddDialogOpen(true)}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Add New Card
              </Button>
            </div>

            {Result.builder(flashcardsResult)
              .onInitialOrWaiting(() => (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">Loading flashcards...</p>
                </div>
              ))
              .onFailure(() => (
                <div className="text-center py-12">
                  <p className="text-destructive">Failed to load flashcards</p>
                </div>
              ))
              .onSuccess(() => {
                if (visibleCards.length === 0) {
                  return (
                    <Card>
                      <CardHeader>
                        <CardTitle>No flashcards yet</CardTitle>
                        <CardDescription>
                          Get started by adding your first flashcard
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button onClick={() => setIsAddDialogOpen(true)}>
                          <PlusIcon className="h-4 w-4 mr-2" />
                          Add First Card
                        </Button>
                      </CardContent>
                    </Card>
                  )
                }

                return (
                  <div className="space-y-4">
                    {visibleCards.map((flashcard, index) => (
                      <FlashcardEditor
                        key={flashcard.id}
                        flashcard={flashcard}
                        onQuestionChange={(value) =>
                          handleUpdateCard(index, 'question', value)
                        }
                        onAnswerChange={(value) =>
                          handleUpdateCard(index, 'answer', value)
                        }
                        onDifficultyChange={(value) =>
                          handleUpdateCard(index, 'difficulty_level', value)
                        }
                        onDelete={() => handleDelete(index)}
                        onMoveUp={() => handleMoveUp(index)}
                        onMoveDown={() => handleMoveDown(index)}
                        canMoveUp={index > 0}
                        canMoveDown={index < visibleCards.length - 1}
                        isDeleted={flashcard.isDeleted}
                      />
                    ))}
                    {localFlashcards
                      .filter((f) => f.isDeleted)
                      .map((flashcard) => (
                        <FlashcardEditor
                          key={`deleted-${flashcard.id}`}
                          flashcard={flashcard}
                          onQuestionChange={() => {}}
                          onAnswerChange={() => {}}
                          onDifficultyChange={() => {}}
                          onDelete={() => {}}
                          onMoveUp={() => {}}
                          onMoveDown={() => {}}
                          canMoveUp={false}
                          canMoveDown={false}
                          isDeleted={true}
                        />
                      ))}
                  </div>
                )
              })
              .render()}
          </div>
        </div>
      </div>

      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Add New Flashcard</DialogTitle>
            <DialogDescription>
              Create a new flashcard for this group
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Question</label>
              <Textarea
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
                placeholder="Enter question..."
                className="min-h-20"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Answer</label>
              <Textarea
                value={newAnswer}
                onChange={(e) => setNewAnswer(e.target.value)}
                placeholder="Enter answer..."
                className="min-h-20"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Difficulty</label>
              <Select
                value={newDifficulty}
                onValueChange={(value) => setNewDifficulty(value)}
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
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setIsAddDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddCard}
                disabled={!newQuestion.trim() || !newAnswer.trim()}
              >
                Add Card
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
