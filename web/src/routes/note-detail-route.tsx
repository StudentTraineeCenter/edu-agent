import { noteDetailRoute } from './_config'
import { NoteDetailPage } from '@/features/note/note-detail-page'

export const NoteDetailRoute = () => {
  const params = noteDetailRoute.useParams()
  return (
    <NoteDetailPage
      noteId={params.noteId}
      projectId={params.projectId}
    />
  )
}

