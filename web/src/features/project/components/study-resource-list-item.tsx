import { Link } from '@tanstack/react-router'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import {
  BrainCircuitIcon,
  FileTextIcon,
  ListChecksIcon,
  MoreVerticalIcon,
  TrashIcon,
  type LucideIcon,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAtomSet } from '@effect-atom/atom-react'
import { deleteFlashcardGroupAtom } from '@/data-acess/flashcard'
import { deleteNoteAtom } from '@/data-acess/note'
import { deleteQuizAtom } from '@/data-acess/quiz'
import { StudyResource } from '@/data-acess/study-resources'
import { useConfirmationDialog } from '@/components/confirmation-dialog'

type Props = {
  studyResource: StudyResource
}

const renderContent = ({
  name,
  created_at,
  icon: Icon,
}: {
  name: string
  created_at: string
  icon: LucideIcon
}) => {
  return (
    <div className="grid grid-cols-6 items-center">
      <div className="flex flex-col w-full col-span-5">
        <div className="flex items-center gap-2">
          <Icon className="size-4" />
          <span>{name}</span>
        </div>
      </div>
      <div className="flex flex-col col-span-1 text-right">
        <span className="text-xs text-muted-foreground">
          {format(new Date(created_at), 'MM/dd HH:mm')}
        </span>
      </div>
    </div>
  )
}

export const StudyResourceListItem = ({ studyResource }: Props) => {
  const deleteFlashcardGroup = useAtomSet(deleteFlashcardGroupAtom, {
    mode: 'promise',
  })
  const deleteQuiz = useAtomSet(deleteQuizAtom, { mode: 'promise' })
  const deleteNote = useAtomSet(deleteNoteAtom, { mode: 'promise' })
  const confirmationDialog = useConfirmationDialog()

  return StudyResource.$match(studyResource, {
    FlashcardGroup: ({ data: flashcardGroup }) => {
      const handleDelete = async (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()

        const confirmed = await confirmationDialog.open({
          title: 'Delete Flashcard Group',
          description: `Are you sure you want to delete "${flashcardGroup.name}"? This action cannot be undone.`,
          confirmLabel: 'Delete',
          cancelLabel: 'Cancel',
          variant: 'destructive',
        })

        if (confirmed) {
          await deleteFlashcardGroup({
            flashcardGroupId: flashcardGroup.id,
            projectId: flashcardGroup.project_id ?? '',
          })
        }
      }

      return (
        <li className="rounded-md p-3 hover:bg-muted/50 group">
          <div className="flex items-center gap-2">
            <Link
              to="/dashboard/p/$projectId/f/$flashcardGroupId"
              params={{
                projectId: flashcardGroup.project_id ?? '',
                flashcardGroupId: flashcardGroup.id,
              }}
              className="flex-1"
            >
              {renderContent({
                name: flashcardGroup.name,
                created_at: flashcardGroup.created_at,
                icon: BrainCircuitIcon,
              })}
            </Link>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVerticalIcon className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleDelete} variant="destructive">
                  <TrashIcon className="size-4" />
                  <span>Delete</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </li>
      )
    },
    Quiz: ({ data: quiz }) => {
      const handleDelete = async (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()

        const confirmed = await confirmationDialog.open({
          title: 'Delete Quiz',
          description: `Are you sure you want to delete "${quiz.name}"? This action cannot be undone.`,
          confirmLabel: 'Delete',
          cancelLabel: 'Cancel',
          variant: 'destructive',
        })

        if (confirmed) {
          await deleteQuiz({
            quizId: quiz.id,
            projectId: quiz.project_id ?? '',
          })
        }
      }

      return (
        <li className="rounded-md p-3 hover:bg-muted/50 group">
          <div className="flex items-center gap-2">
            <Link
              to="/dashboard/p/$projectId/q/$quizId"
              params={{
                projectId: quiz.project_id ?? '',
                quizId: quiz.id,
              }}
              className="flex-1"
            >
              {renderContent({
                name: quiz.name,
                created_at: quiz.created_at,
                icon: ListChecksIcon,
              })}
            </Link>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVerticalIcon className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleDelete} variant="destructive">
                  <TrashIcon className="size-4" />
                  <span>Delete</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </li>
      )
    },
    Note: ({ data: note }) => {
      const handleDelete = async (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()

        const confirmed = await confirmationDialog.open({
          title: 'Delete Note',
          description: `Are you sure you want to delete "${note.title}"? This action cannot be undone.`,
          confirmLabel: 'Delete',
          cancelLabel: 'Cancel',
          variant: 'destructive',
        })

        if (confirmed) {
          await deleteNote({
            noteId: note.id,
            projectId: note.project_id ?? '',
          })
        }
      }

      return (
        <li className="rounded-md p-3 hover:bg-muted/50 group">
          <div className="flex items-center gap-2">
            <Link
              to="/dashboard/p/$projectId/n/$noteId"
              params={{
                projectId: note.project_id ?? '',
                noteId: note.id,
              }}
              className="flex-1"
            >
              {renderContent({
                name: note.title,
                created_at: note.created_at,
                icon: FileTextIcon,
              })}
            </Link>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVerticalIcon className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleDelete} variant="destructive">
                  <TrashIcon className="size-4" />
                  <span>Delete</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </li>
      )
    },
  })
}
