import { useAtomValue } from '@effect-atom/atom-react'
import { studyPlanAtom } from '@/data-acess/study-plan'
import { Result } from '@effect-atom/atom-react'
import { Loader2Icon } from 'lucide-react'
import { StudyPlanView } from './study-plan-view'
import { Button } from '@/components/ui/button'
import { useAtomSet } from '@effect-atom/atom-react'
import { generateStudyPlanAtom } from '@/data-acess/study-plan'
import { useState } from 'react'

type StudyPlanContentProps = {
  projectId: string
  className?: string
}

export const StudyPlanContent = ({
  projectId,
  className,
}: StudyPlanContentProps) => {
  const studyPlanResult = useAtomValue(studyPlanAtom(projectId))
  const generatePlan = useAtomSet(generateStudyPlanAtom, { mode: 'promise' })
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      await generatePlan({ projectId })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className={className}>
      {Result.builder(studyPlanResult)
        .onInitialOrWaiting(() => (
          <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
            <Loader2Icon className="size-4 animate-spin" />
            <span>Loading study plan...</span>
          </div>
        ))
        .onFailure(() => (
          <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
            <span>Failed to load study plan</span>
          </div>
        ))
        .onSuccess((plan) => {
          if (!plan) {
            return (
              <div className="flex flex-1 flex-col items-center justify-center gap-4 text-muted-foreground">
                <p>No study plan found. Generate one to get started.</p>
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <Loader2Icon className="size-4 mr-2 animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <span>Generate Study Plan</span>
                  )}
                </Button>
              </div>
            )
          }

          return <StudyPlanView plan={plan} />
        })
        .render()}
    </div>
  )
}

