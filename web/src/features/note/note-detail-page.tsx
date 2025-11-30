import { NoteHeader } from './components/note-header'
import { NoteContent } from './components/note-content'

type NoteDetailPageProps = {
  noteId: string
  projectId: string
}

export const NoteDetailPage = ({
  noteId,
  projectId,
}: NoteDetailPageProps) => {
  return (
    <div className="flex h-full flex-col">
      <NoteHeader noteId={noteId} projectId={projectId} />

      <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
        <div className="max-w-5xl mx-auto w-full flex flex-col flex-1 min-h-0 p-4">
          <NoteContent noteId={noteId} className="flex-1" />
        </div>
      </div>
    </div>
  )
}

