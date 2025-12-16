import { useNavigate } from '@tanstack/react-router'
import { ArrowLeft, BrainIcon, Clock, Loader2Icon, Target } from 'lucide-react'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Button } from '@/components/ui/button'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getStudySessionAtom } from '@/data-acess/adaptive-learning'

type StudySessionDetailPageProps = {
  sessionId: string
  projectId: string
}

export const StudySessionDetailPage = ({
  sessionId,
  projectId,
}: StudySessionDetailPageProps) => {
  const navigate = useNavigate()
  const sessionResult = useAtomValue(getStudySessionAtom(sessionId))

  const handleBack = () => {
    navigate({
      to: '/dashboard/p/$projectId',
      params: { projectId },
    })
  }

  return (
    <div className="flex h-full flex-col">
      <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
        <div className="flex flex-1 items-center gap-2 px-3">
          <SidebarTrigger />
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            onClick={handleBack}
          >
            <ArrowLeft className="size-4" />
            <span className="sr-only">Back to project</span>
          </Button>
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="line-clamp-1 font-medium">
                  Study Session
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>
      </header>

      <div className="flex flex-1 flex-col min-h-0 overflow-auto p-4">
        <div className="max-w-4xl mx-auto w-full space-y-6 py-8">
          {Result.builder(sessionResult)
            .onInitialOrWaiting(() => (
              <div className="flex items-center justify-center gap-2 text-muted-foreground py-12">
                <Loader2Icon className="size-4 animate-spin" />
                <span>Loading study session...</span>
              </div>
            ))
            .onFailure(() => (
              <div className="text-center space-y-4 py-12">
                <p className="text-destructive">Failed to load study session</p>
                <Button onClick={handleBack} variant="outline">
                  Back to Project
                </Button>
              </div>
            ))
            .onSuccess((sessionData) => (
              <>
                <div className="text-center space-y-2">
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <BrainIcon className="h-8 w-8 text-primary" />
                    <h1 className="text-3xl font-bold">Study Session</h1>
                  </div>
                  <p className="text-muted-foreground">
                    Personalized study session based on your performance
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Estimated Time
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">
                        {sessionData.estimated_time_minutes} minutes
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <BrainIcon className="h-5 w-5" />
                        Flashcards
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">TODO COUNT</p>
                    </CardContent>
                  </Card>
                </div>

                {sessionData.focus_topics &&
                  sessionData.focus_topics.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Target className="h-5 w-5" />
                          Focus Topics
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-2">
                          {sessionData.focus_topics.map((topic, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                {Array.isArray(sessionData.session_data.learning_objectives) &&
                  sessionData.session_data.learning_objectives.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Learning Objectives</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {(
                            sessionData.session_data
                              .learning_objectives as Array<string>
                          ).map((objective: string, idx: number) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-primary mt-1">•</span>
                              <span>{objective}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}

                <div className="flex justify-center gap-4 pt-4">
                  <Button onClick={handleBack} variant="outline">
                    Back to Project
                  </Button>
                  <Button
                    onClick={() => {
                      // Navigate to the study session's flashcard group
                      // Check if flashcard_group_id is in session_data
                      const flashcardGroupId = (
                        sessionData.session_data as Record<string, unknown>
                      ).flashcard_group_id as string | undefined
                      if (flashcardGroupId) {
                        navigate({
                          to: '/dashboard/p/$projectId/f/$flashcardGroupId',
                          params: {
                            projectId,
                            flashcardGroupId,
                          },
                        })
                      } else {
                        handleBack()
                      }
                    }}
                  >
                    Start Studying
                  </Button>
                </div>
              </>
            ))
            .render()}
        </div>
      </div>
    </div>
  )
}
