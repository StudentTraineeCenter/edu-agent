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
import { Loader2Icon, PlusIcon, Clock, BrainIcon } from 'lucide-react'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { Result } from '@effect-atom/atom-react'
import { listStudySessionsAtom } from '@/data-acess/adaptive-learning'
import { generateStudySessionAtom } from '@/data-acess/adaptive-learning'
import { useNavigate } from '@tanstack/react-router'
import type { StudySessionResponse } from '@/integrations/api/client'

type StudySessionsDialogStore = {
  isOpen: boolean
  projectId: string | null
  open: (projectId: string) => void
  close: () => void
}

export const useStudySessionsDialog = create<StudySessionsDialogStore>(
  (set) => ({
    isOpen: false,
    projectId: null,
    open: (projectId: string) => set({ isOpen: true, projectId }),
    close: () => set({ isOpen: false, projectId: null }),
  }),
)

export function StudySessionsDialog() {
  const { isOpen, projectId, close } = useStudySessionsDialog()
  const [isCreating, setIsCreating] = useState(false)
  const navigate = useNavigate()

  const sessionsResult = useAtomValue(listStudySessionsAtom(projectId || ''))
  const generateSession = useAtomSet(generateStudySessionAtom, {
    mode: 'promise',
  })

  const handleCreateNew = async () => {
    if (!projectId) return

    setIsCreating(true)
    try {
      const session = await generateSession({
        projectId,
        sessionLengthMinutes: 30,
      })
      close()
      navigate({
        to: '/dashboard/p/$projectId/study-session/$sessionId',
        params: { projectId, sessionId: session.session_id },
      })
    } catch (error) {
      console.error('Failed to create study session:', error)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && close()}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Study Sessions</DialogTitle>
          <DialogDescription>
            View and manage your study sessions. Click on a session to open it.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 border rounded-md overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto p-4">
            {Result.builder(sessionsResult)
              .onInitialOrWaiting(() => (
                <div className="flex items-center gap-2 text-muted-foreground py-4">
                  <Loader2Icon className="size-4 animate-spin" />
                  <span>Loading study sessions…</span>
                </div>
              ))
              .onFailure(() => (
                <div className="text-destructive py-4">
                  Failed to load study sessions
                </div>
              ))
              .onSuccess((sessions) => {
                if (sessions.length === 0) {
                  return (
                    <div className="text-muted-foreground py-4 text-center">
                      No study sessions yet. Create your first one to get
                      started.
                    </div>
                  )
                }

                return (
                  <div className="space-y-3">
                    {sessions.map((session) => (
                      <StudySessionItem
                        key={session.session_id}
                        session={session}
                        projectId={projectId || ''}
                      />
                    ))}
                  </div>
                )
              })
              .render()}
          </div>
        </div>

        <DialogFooter className="gap-2 shrink-0">
          <Button
            type="button"
            variant="outline"
            onClick={close}
            disabled={isCreating}
          >
            Close
          </Button>
          <Button type="button" onClick={handleCreateNew} disabled={isCreating}>
            {isCreating ? (
              <>
                <Loader2Icon className="size-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <PlusIcon className="size-4" />
                <span>Create New Session</span>
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

type StudySessionItemProps = {
  session: StudySessionResponse
  projectId: string
}

function StudySessionItem({ session, projectId }: StudySessionItemProps) {
  const navigate = useNavigate()

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(date)
  }

  if (!projectId) return null

  return (
    <button
      onClick={() =>
        navigate({
          to: '/dashboard/p/$projectId/study-session/$sessionId',
          params: { projectId, sessionId: session.session_id },
        })
      }
      className="w-full text-left p-3 rounded-md border hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <BrainIcon className="size-4 text-primary shrink-0" />
            <span className="text-sm font-medium truncate">Study Session</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Clock className="size-3" />
              <span>{session.estimated_time_minutes} min</span>
            </div>
            <div className="flex items-center gap-1">
              <BrainIcon className="size-3" />
              <span>{session.flashcards.length} flashcards</span>
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {formatDate(session.generated_at)}
          </div>
        </div>
      </div>
    </button>
  )
}
