import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  generateStudyPlanAtom,
  latestStudyPlanRemoteAtom,
  studyPlansHistoryRemoteAtom,
} from '@/data-acess/study-plan'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { Link } from '@tanstack/react-router'
import {
  BrainCircuit,
  CalendarDays,
  History,
  Loader2,
  Sparkles,
} from 'lucide-react'
import { useState } from 'react'
import { StudyPlanHeader } from './components/study-plan-header'

interface StudyPlanPageProps {
  projectId: string
}

export const StudyPlanPage = ({ projectId }: StudyPlanPageProps) => {
  const latestPlanResult = useAtomValue(latestStudyPlanRemoteAtom(projectId))
  const historyResult = useAtomValue(studyPlansHistoryRemoteAtom(projectId))

  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  // Determine which plan to show: selected or latest
  const historyPlans = Result.isSuccess(historyResult)
    ? historyResult.value
    : []
  const latestPlan = Result.isSuccess(latestPlanResult)
    ? latestPlanResult.value
    : null

  const displayedPlan = selectedPlanId
    ? historyPlans.find((p) => p.id === selectedPlanId)
    : latestPlan

  // Update selected plan if we just loaded history and possess a latest plan but weren't selecting anything
  // Actually, default behavior is to show latestPlan if selectedPlanId is null.

  const generatePlan = useAtomSet(generateStudyPlanAtom, {
    mode: 'promise',
  })

  const handleGenerate = () => {
    setIsGenerating(true)
    generatePlan(projectId)
  }

  return (
    <div className="flex h-full flex-col max-h-screen">
      <StudyPlanHeader projectId={projectId} />
      <div className="flex flex-1 flex-col min-h-0 overflow-y-auto">
        <div className="container mx-auto max-w-5xl py-8 space-y-8">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
            <div>
              <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                <BrainCircuit className="h-8 w-8 text-primary" />
                Personalized Study Plan
              </h1>
              <p className="text-muted-foreground mt-1">
                AI-driven analysis of your performance to optimize your learning
                path.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {historyPlans.length > 0 && (
                <Select
                  value={selectedPlanId || 'latest'}
                  onValueChange={(val) =>
                    setSelectedPlanId(val === 'latest' ? null : val)
                  }
                >
                  <SelectTrigger className="w-[180px]">
                    <History className="mr-2 h-4 w-4" />
                    <SelectValue placeholder="History" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="latest">Latest Plan</SelectItem>
                    {historyPlans.map((plan) => (
                      <SelectItem key={plan.id} value={plan.id}>
                        {new Date(plan.created_at).toLocaleDateString()}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <Button
                onClick={handleGenerate}
                disabled={isGenerating}
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate New Plan
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="grid gap-6">
            {displayedPlan ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <Card className="border shadow-lg">
                    <CardHeader className="border-b">
                      <CardTitle className="text-xl flex items-center gap-2">
                        <CalendarDays className="h-5 w-5 text-primary" />
                        Your Structured Plan
                      </CardTitle>
                      <CardDescription>
                        Generated on{' '}
                        {new Date(displayedPlan.created_at).toLocaleString()}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6 space-y-6">
                      {/* Analysis */}
                      <div>
                        <h3 className="text-lg font-semibold mb-2">Analysis</h3>
                        <p className="text-muted-foreground">
                          {displayedPlan.content.analysis}
                        </p>
                      </div>

                      {/* Focus Areas */}
                      <div>
                        <h3 className="text-lg font-semibold mb-2">
                          Focus Areas
                        </h3>
                        <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                          {displayedPlan.content.focus_areas.map((area, i) => (
                            <li key={i}>{area}</li>
                          ))}
                        </ol>
                      </div>

                      {/* Action Items */}
                      <div>
                        <h3 className="text-lg font-semibold mb-2">
                          Action Items
                        </h3>
                        <div className="grid gap-2">
                          {displayedPlan.content.action_items.map((item, i) => {
                            const isQuiz = item.type === 'quiz'
                            return (
                              <Link
                                key={i}
                                to={
                                  isQuiz
                                    ? '/dashboard/p/$projectId/q/$quizId'
                                    : '/dashboard/p/$projectId/f/$flashcardGroupId'
                                }
                                params={
                                  isQuiz
                                    ? {
                                        projectId,
                                        quizId: item.parent_id || item.id,
                                      }
                                    : {
                                        projectId,
                                        flashcardGroupId:
                                          item.parent_id || item.id,
                                      }
                                }
                                className="block"
                              >
                                <div className="flex items-center gap-2 p-3 rounded-md bg-muted/50 hover:bg-muted transition-colors border">
                                  {isQuiz ? (
                                    <BrainCircuit className="h-4 w-4 text-blue-500" />
                                  ) : (
                                    <Sparkles className="h-4 w-4 text-amber-500" />
                                  )}
                                  <div className="flex-1">
                                    <div className="font-medium text-sm">
                                      {item.title}
                                    </div>
                                    {item.description && (
                                      <div className="text-xs text-muted-foreground">
                                        {item.description}
                                      </div>
                                    )}
                                  </div>
                                  <span className="text-xs uppercase tracking-wider font-bold text-muted-foreground opacity-70 border px-1.5 py-0.5 rounded">
                                    {item.type}
                                  </span>
                                </div>
                              </Link>
                            )
                          })}
                        </div>
                      </div>

                      {/* Schedule */}
                      <div>
                        <h3 className="text-lg font-semibold mb-2">
                          Weekly Schedule
                        </h3>
                        <div className="space-y-4">
                          {displayedPlan.content.schedule.map((day, i) => (
                            <div
                              key={i}
                              className="border-l-2 border-primary/20 pl-4 py-1"
                            >
                              <div className="font-medium text-sm">
                                {day.day}
                              </div>
                              <ul className="list-disc list-inside text-sm text-muted-foreground mt-1">
                                {day.tasks.map((task, j) => (
                                  <li key={j}>{task}</li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Encouragement */}
                      <div className="bg-primary/5 p-4 rounded-lg border border-primary/10">
                        <p className="font-medium text-primary italic text-center">
                          "{displayedPlan.content.encouragement}"
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Weak Topics</CardTitle>
                      <CardDescription>
                        Areas needing improvement
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {displayedPlan.weak_topics &&
                      displayedPlan.weak_topics.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {displayedPlan.weak_topics.map((topic, i) => (
                            <span
                              key={i}
                              className="px-3 py-1 rounded-full bg-destructive/10 text-destructive text-sm font-medium"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No specific weak topics identified yet. Keep
                          practicing!
                        </p>
                      )}
                    </CardContent>
                  </Card>

                  <Card className="bg-muted/50">
                    <CardHeader>
                      <CardTitle className="text-lg">How it works</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground space-y-2">
                      <p>
                        1. We analyze your quiz results and flashcard
                        performance.
                      </p>
                      <p>
                        2. We identify topics where your accuracy is below 70%.
                      </p>
                      <p>
                        3. Our AI agent creates a custom schedule and recommends
                        specific resources.
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8 border-2 border-dashed rounded-lg bg-muted/30">
                <div className="bg-background p-4 rounded-full shadow-sm mb-4">
                  <BrainCircuit className="h-12 w-12 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">
                  No Study Plan Yet
                </h3>
                <p className="text-muted-foreground max-w-md mb-6">
                  Generate your first personalized study plan to get a tailored
                  roadmap for your learning journey based on your performance.
                </p>
                <Button onClick={handleGenerate} disabled={isGenerating}>
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    'Generate My First Plan'
                  )}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
