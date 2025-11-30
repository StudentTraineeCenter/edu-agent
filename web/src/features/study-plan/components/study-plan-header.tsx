import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { studyPlanAtom, generateStudyPlanAtom } from '@/data-acess/study-plan'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ArrowLeft, RefreshCwIcon, Loader2Icon } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { format } from 'date-fns'
import { useState } from 'react'

const StudyPlanHeaderContent = ({ projectId }: { projectId: string }) => {
  const studyPlanResult = useAtomValue(studyPlanAtom(projectId))

  return Result.builder(studyPlanResult)
    .onSuccess((plan) => {
      if (!plan) {
        return (
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="line-clamp-1 font-medium">
                  Study Plan
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        )
      }

      return (
        <div className="flex items-center gap-4">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="line-clamp-1 font-medium">
                  {plan.title}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <span className="text-xs text-muted-foreground">
            Generated:{' '}
            {format(new Date(plan.generated_at), 'MMM dd, yyyy HH:mm')}
          </span>
        </div>
      )
    })
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .onFailure(() => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              Study Plan
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

type StudyPlanHeaderProps = {
  projectId: string
}

export const StudyPlanHeader = ({ projectId }: StudyPlanHeaderProps) => {
  const generatePlan = useAtomSet(generateStudyPlanAtom, { mode: 'promise' })
  const studyPlanResult = useAtomValue(studyPlanAtom(projectId))
  const [isRegenerating, setIsRegenerating] = useState(false)

  const handleRegenerate = async () => {
    setIsRegenerating(true)
    try {
      await generatePlan({ projectId })
      // Atom se automaticky refreshne
    } finally {
      setIsRegenerating(false)
    }
  }

  return (
    <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        <SidebarTrigger />
        <Button variant="ghost" size="icon" className="size-7" asChild>
          <Link to="/dashboard/p/$projectId" params={{ projectId }}>
            <ArrowLeft className="size-4" />
            <span className="sr-only">Back to project</span>
          </Link>
        </Button>
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <StudyPlanHeaderContent projectId={projectId} />
      </div>
      {Result.isSuccess(studyPlanResult) && studyPlanResult.value && (
        <div className="flex items-center gap-2 px-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRegenerate}
            disabled={isRegenerating}
          >
            {isRegenerating ? (
              <>
                <Loader2Icon className="size-4 mr-2 animate-spin" />
                <span>Regenerating...</span>
              </>
            ) : (
              <>
                <RefreshCwIcon className="size-4 mr-2" />
                <span>Regenerate</span>
              </>
            )}
          </Button>
        </div>
      )}
    </header>
  )
}

