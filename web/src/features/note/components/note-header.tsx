import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue } from '@effect-atom/atom-react'
import { noteAtom } from '@/data-acess/note'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import { Link } from '@tanstack/react-router'

type NoteHeaderContentProps = {
  noteId: string
  projectId: string
}

const NoteHeaderContent = ({ noteId, projectId }: NoteHeaderContentProps) => {
  const noteResult = useAtomValue(noteAtom({ projectId, noteId }))

  return Result.builder(noteResult)
    .onSuccess((note) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {note.title || 'Note'}
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
              Note
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

type NoteHeaderProps = {
  noteId: string
  projectId: string
}

export const NoteHeader = ({ noteId, projectId }: NoteHeaderProps) => {
  const noteResult = useAtomValue(noteAtom({ projectId, noteId }))

  return (
    <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(noteResult) && (
          <>
            <SidebarTrigger />
            <Button variant="ghost" size="icon" className="size-7" asChild>
              <Link to="/dashboard/p/$projectId" params={{ projectId }}>
                <ArrowLeft className="size-4" />
                <span className="sr-only">Back to project</span>
              </Link>
            </Button>
          </>
        )}
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <NoteHeaderContent noteId={noteId} projectId={projectId} />
      </div>
    </header>
  )
}
