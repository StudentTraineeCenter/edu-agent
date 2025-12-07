import { useAtomValue } from '@effect-atom/atom-react'
import { noteAtom } from '@/data-acess/note'
import { Result } from '@effect-atom/atom-react'
import { Loader2Icon } from 'lucide-react'
import { Response } from '@/components/ai-elements/response'

type NoteContentProps = {
  noteId: string
  className?: string
}

export const NoteContent = ({ noteId, className }: NoteContentProps) => {
  const noteResult = useAtomValue(noteAtom(noteId))

  return Result.builder(noteResult)
    .onInitialOrWaiting(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading note...</span>
      </div>
    ))
    .onFailure(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
        <span>Failed to load note</span>
      </div>
    ))
    .onSuccess((result) => {
      const note = result.note
      if (!note) {
        return (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            <p>Note not found</p>
          </div>
        )
      }

      return (
        <div className={`flex flex-col space-y-4 ${className || ''}`}>
          {note.description && (
            <div className="text-muted-foreground text-sm">
              {note.description}
            </div>
          )}
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <Response>{note.content}</Response>
          </div>
        </div>
      )
    })
    .render()
}
