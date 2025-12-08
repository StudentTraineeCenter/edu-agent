import { useAtomValue, useAtomSet, useAtom } from '@effect-atom/atom-react'
import { Result } from '@effect-atom/atom-react'
import {
  quizQuestionsAtom,
  createQuizQuestionAtom,
  updateQuizQuestionAtom,
  reorderQuizQuestionsAtom,
  deleteQuizQuestionAtom,
} from '@/data-acess/quiz'
import { quizAtom } from '@/data-acess/quiz'
import { Link } from '@tanstack/react-router'
import { ArrowLeft, PlusIcon, SaveIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { QuizQuestionEditor } from './components/quiz-question-editor'
import { useState, useCallback, useEffect, useMemo } from 'react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
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
import type { QuizQuestionDto } from '@/integrations/api/client'

type QuizEditPageProps = {
  quizId: string
  projectId: string
}

type LocalQuestion = {
  id: string
  question_text: string
  option_a: string
  option_b: string
  option_c: string
  option_d: string
  correct_option: string
  explanation?: string | null
  difficulty_level: string
  position: number
  isNew?: boolean
  isDeleted?: boolean
  originalId?: string
}

const QuizHeaderContent = ({ quizId }: { quizId: string }) => {
  const quizResult = useAtomValue(quizAtom(quizId))

  return Result.builder(quizResult)
    .onSuccess((res) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              Edit: {res.quiz?.name || 'Quiz'}
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
              Edit Quiz
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

export const QuizEditPage = ({ quizId, projectId }: QuizEditPageProps) => {
  const questionsResult = useAtomValue(quizQuestionsAtom(quizId))
  const quizResult = useAtomValue(quizAtom(quizId))
  const [createQuestionResult, createQuestion] = useAtom(
    createQuizQuestionAtom,
    { mode: 'promise' },
  )
  const [updateQuestionResult, updateQuestion] = useAtom(
    updateQuizQuestionAtom,
    { mode: 'promise' },
  )
  const reorderQuestions = useAtomSet(reorderQuizQuestionsAtom, {
    mode: 'promise',
  })
  const deleteQuestion = useAtomSet(deleteQuizQuestionAtom, {
    mode: 'promise',
  })

  // Local state for all questions
  const [localQuestions, setLocalQuestions] = useState<LocalQuestion[]>([])
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [newQuestionText, setNewQuestionText] = useState('')
  const [newOptionA, setNewOptionA] = useState('')
  const [newOptionB, setNewOptionB] = useState('')
  const [newOptionC, setNewOptionC] = useState('')
  const [newOptionD, setNewOptionD] = useState('')
  const [newCorrectOption, setNewCorrectOption] = useState('a')
  const [newExplanation, setNewExplanation] = useState('')
  const [newDifficulty, setNewDifficulty] = useState('medium')
  const [nextTempId, setNextTempId] = useState(1)

  // Initialize local questions from server data
  useEffect(() => {
    if (Result.isSuccess(questionsResult)) {
      const questions = questionsResult.value
      setLocalQuestions(
        questions.map((q) => ({
          id: q.id,
          question_text: q.question_text,
          option_a: q.option_a,
          option_b: q.option_b,
          option_c: q.option_c,
          option_d: q.option_d,
          correct_option: q.correct_option,
          explanation: q.explanation,
          difficulty_level: q.difficulty_level,
          position: q.position,
        })),
      )
    }
  }, [questionsResult])

  // Check if there are unsaved changes
  const hasUnsavedChanges = useMemo(() => {
    if (!Result.isSuccess(questionsResult)) return false

    const original = questionsResult.value
    const current = localQuestions.filter((q) => !q.isDeleted)

    // Check for new questions
    const hasNew = localQuestions.some((q) => q.isNew)

    // Check for deleted questions
    const hasDeleted = localQuestions.some((q) => q.isDeleted)

    // Check for modified questions
    const hasModified = original.some((orig) => {
      const local = localQuestions.find((l) => l.id === orig.id && !l.isDeleted)
      if (!local) return false
      return (
        local.question_text !== orig.question_text ||
        local.option_a !== orig.option_a ||
        local.option_b !== orig.option_b ||
        local.option_c !== orig.option_c ||
        local.option_d !== orig.option_d ||
        local.correct_option !== orig.correct_option ||
        local.explanation !== (orig.explanation || null) ||
        local.difficulty_level !== orig.difficulty_level
      )
    })

    // Check for reordered questions
    const originalIds = original.map((q) => q.id)
    const currentIds = current.map((q) => q.id)
    const hasReordered =
      JSON.stringify(originalIds) !== JSON.stringify(currentIds)

    return hasNew || hasDeleted || hasModified || hasReordered
  }, [questionsResult, localQuestions])

  const handleAddQuestion = () => {
    if (
      !newQuestionText.trim() ||
      !newOptionA.trim() ||
      !newOptionB.trim() ||
      !newOptionC.trim() ||
      !newOptionD.trim()
    )
      return

    const newQ: LocalQuestion = {
      id: `temp-${nextTempId}`,
      question_text: newQuestionText,
      option_a: newOptionA,
      option_b: newOptionB,
      option_c: newOptionC,
      option_d: newOptionD,
      correct_option: newCorrectOption,
      explanation: newExplanation || null,
      difficulty_level: newDifficulty,
      position: localQuestions.length,
      isNew: true,
      originalId: `temp-${nextTempId}`,
    }

    setLocalQuestions((prev) => [...prev, newQ])
    setNextTempId((prev) => prev + 1)
    setNewQuestionText('')
    setNewOptionA('')
    setNewOptionB('')
    setNewOptionC('')
    setNewOptionD('')
    setNewCorrectOption('a')
    setNewExplanation('')
    setNewDifficulty('medium')
    setIsAddDialogOpen(false)
  }

  const handleDelete = useCallback((index: number) => {
    setLocalQuestions((prev) => {
      const updated = [...prev]
      const question = updated[index]
      if (question.isNew) {
        // Remove new questions completely
        updated.splice(index, 1)
      } else {
        // Mark existing questions as deleted
        updated[index] = { ...question, isDeleted: true }
      }
      return updated
    })
  }, [])

  const handleMoveUp = useCallback((index: number) => {
    if (index === 0) return
    setLocalQuestions((prev) => {
      const updated = [...prev]
      ;[updated[index - 1], updated[index]] = [
        updated[index],
        updated[index - 1],
      ]
      // Update positions
      return updated.map((q, idx) => ({ ...q, position: idx }))
    })
  }, [])

  const handleMoveDown = useCallback((index: number) => {
    setLocalQuestions((prev) => {
      if (index >= prev.length - 1) return prev
      const updated = [...prev]
      ;[updated[index], updated[index + 1]] = [
        updated[index + 1],
        updated[index],
      ]
      // Update positions
      return updated.map((q, idx) => ({ ...q, position: idx }))
    })
  }, [])

  const handleUpdateQuestion = useCallback(
    (
      index: number,
      field:
        | 'question_text'
        | 'option_a'
        | 'option_b'
        | 'option_c'
        | 'option_d'
        | 'correct_option'
        | 'explanation'
        | 'difficulty_level',
      value: string,
    ) => {
      setLocalQuestions((prev) => {
        const updated = [...prev]
        updated[index] = { ...updated[index], [field]: value }
        return updated
      })
    },
    [],
  )

  const handleSave = async () => {
    if (!hasUnsavedChanges) return

    const activeQuestions = localQuestions.filter((q) => !q.isDeleted)
    const original = Result.isSuccess(questionsResult)
      ? questionsResult.value
      : []

    try {
      // 1. Delete removed questions
      const toDelete = original.filter(
        (orig) => !activeQuestions.find((active) => active.id === orig.id),
      )
      for (const question of toDelete) {
        await deleteQuestion({
          questionId: question.id,
          quizId,
        })
      }

      // 2. Create new questions
      const toCreate = activeQuestions.filter((q) => q.isNew)
      for (const question of toCreate) {
        await createQuestion({
          quizId,
          questionText: question.question_text,
          optionA: question.option_a,
          optionB: question.option_b,
          optionC: question.option_c,
          optionD: question.option_d,
          correctOption: question.correct_option,
          explanation: question.explanation || undefined,
          difficultyLevel: question.difficulty_level,
          position: question.position,
        })
      }

      // 3. Update modified questions
      const toUpdate = activeQuestions.filter((question) => {
        if (question.isNew) return false
        const orig = original.find((o) => o.id === question.id)
        if (!orig) return false
        return (
          question.question_text !== orig.question_text ||
          question.option_a !== orig.option_a ||
          question.option_b !== orig.option_b ||
          question.option_c !== orig.option_c ||
          question.option_d !== orig.option_d ||
          question.correct_option !== orig.correct_option ||
          question.explanation !== (orig.explanation || null) ||
          question.difficulty_level !== orig.difficulty_level
        )
      })
      for (const question of toUpdate) {
        await updateQuestion({
          questionId: question.id,
          quizId,
          questionText: question.question_text,
          optionA: question.option_a,
          optionB: question.option_b,
          optionC: question.option_c,
          optionD: question.option_d,
          correctOption: question.correct_option,
          explanation: question.explanation || undefined,
          difficultyLevel: question.difficulty_level,
        })
      }

      // 4. Reorder if needed
      const originalIds = original.map((q) => q.id)
      const currentIds = activeQuestions
        .filter((q) => !q.isNew)
        .map((q) => q.id)
      const hasReordered =
        JSON.stringify(originalIds) !== JSON.stringify(currentIds)

      if (hasReordered) {
        await reorderQuestions({
          quizId,
          questionIds: activeQuestions.filter((q) => !q.isNew).map((q) => q.id),
        })
      }
    } catch (error) {
      console.error('Failed to save changes:', error)
    }
  }

  const visibleQuestions = localQuestions.filter((q) => !q.isDeleted)

  return (
    <div className="flex h-full flex-col">
      <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2 z-10">
        <div className="flex flex-1 items-center gap-2 px-3">
          {Result.isSuccess(quizResult) && (
            <>
              <SidebarTrigger />
              <Button variant="ghost" size="icon" className="size-7" asChild>
                <Link
                  to="/dashboard/p/$projectId/q/$quizId"
                  params={{ projectId, quizId }}
                >
                  <ArrowLeft className="size-4" />
                  <span className="sr-only">Back to quiz</span>
                </Link>
              </Button>
            </>
          )}
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <QuizHeaderContent quizId={quizId} />
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
              updateQuestionResult.waiting ||
              createQuestionResult.waiting
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
                  Edit Quiz Questions
                </h1>
                <p className="text-muted-foreground mt-2">
                  Add, edit, and reorder your quiz questions. Click "Save All"
                  when done.
                </p>
              </div>
              <Button onClick={() => setIsAddDialogOpen(true)}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Add New Question
              </Button>
            </div>

            {Result.builder(questionsResult)
              .onInitialOrWaiting(() => (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">Loading questions...</p>
                </div>
              ))
              .onFailure(() => (
                <div className="text-center py-12">
                  <p className="text-destructive">Failed to load questions</p>
                </div>
              ))
              .onSuccess(() => {
                if (visibleQuestions.length === 0) {
                  return (
                    <Card>
                      <CardHeader>
                        <CardTitle>No questions yet</CardTitle>
                        <CardDescription>
                          Get started by adding your first question
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button onClick={() => setIsAddDialogOpen(true)}>
                          <PlusIcon className="h-4 w-4 mr-2" />
                          Add First Question
                        </Button>
                      </CardContent>
                    </Card>
                  )
                }

                return (
                  <div className="space-y-4">
                    {visibleQuestions.map((question, index) => (
                      <QuizQuestionEditor
                        key={question.id}
                        question={question}
                        onQuestionTextChange={(value) =>
                          handleUpdateQuestion(index, 'question_text', value)
                        }
                        onOptionAChange={(value) =>
                          handleUpdateQuestion(index, 'option_a', value)
                        }
                        onOptionBChange={(value) =>
                          handleUpdateQuestion(index, 'option_b', value)
                        }
                        onOptionCChange={(value) =>
                          handleUpdateQuestion(index, 'option_c', value)
                        }
                        onOptionDChange={(value) =>
                          handleUpdateQuestion(index, 'option_d', value)
                        }
                        onCorrectOptionChange={(value) =>
                          handleUpdateQuestion(index, 'correct_option', value)
                        }
                        onExplanationChange={(value) =>
                          handleUpdateQuestion(index, 'explanation', value)
                        }
                        onDifficultyChange={(value) =>
                          handleUpdateQuestion(index, 'difficulty_level', value)
                        }
                        onDelete={() => handleDelete(index)}
                        onMoveUp={() => handleMoveUp(index)}
                        onMoveDown={() => handleMoveDown(index)}
                        canMoveUp={index > 0}
                        canMoveDown={index < visibleQuestions.length - 1}
                        isDeleted={question.isDeleted}
                      />
                    ))}
                    {localQuestions
                      .filter((q) => q.isDeleted)
                      .map((question) => (
                        <QuizQuestionEditor
                          key={`deleted-${question.id}`}
                          question={question}
                          onQuestionTextChange={() => {}}
                          onOptionAChange={() => {}}
                          onOptionBChange={() => {}}
                          onOptionCChange={() => {}}
                          onOptionDChange={() => {}}
                          onCorrectOptionChange={() => {}}
                          onExplanationChange={() => {}}
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
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle>Add New Question</DialogTitle>
            <DialogDescription>
              Create a new question for this quiz
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Question</label>
              <Textarea
                value={newQuestionText}
                onChange={(e) => setNewQuestionText(e.target.value)}
                placeholder="Enter question..."
                className="min-h-20"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Option A</label>
                <Input
                  value={newOptionA}
                  onChange={(e) => setNewOptionA(e.target.value)}
                  placeholder="Option A"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Option B</label>
                <Input
                  value={newOptionB}
                  onChange={(e) => setNewOptionB(e.target.value)}
                  placeholder="Option B"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Option C</label>
                <Input
                  value={newOptionC}
                  onChange={(e) => setNewOptionC(e.target.value)}
                  placeholder="Option C"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Option D</label>
                <Input
                  value={newOptionD}
                  onChange={(e) => setNewOptionD(e.target.value)}
                  placeholder="Option D"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Correct Option</label>
              <Select
                value={newCorrectOption}
                onValueChange={(value) => setNewCorrectOption(value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="a">A</SelectItem>
                  <SelectItem value="b">B</SelectItem>
                  <SelectItem value="c">C</SelectItem>
                  <SelectItem value="d">D</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Explanation (optional)
              </label>
              <Textarea
                value={newExplanation}
                onChange={(e) => setNewExplanation(e.target.value)}
                placeholder="Enter explanation..."
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
                onClick={handleAddQuestion}
                disabled={
                  !newQuestionText.trim() ||
                  !newOptionA.trim() ||
                  !newOptionB.trim() ||
                  !newOptionC.trim() ||
                  !newOptionD.trim()
                }
              >
                Add Question
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
