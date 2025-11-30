import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

type StudyPlan = {
  id: string
  user_id: string
  project_id: string
  title: string
  description?: string | null
  plan_content: unknown
  generated_at: string
  updated_at: string
}

type StudyPlanViewProps = {
  plan: StudyPlan
}

type PlanContent = {
  weak_topics?: Array<{
    topic: string
    accuracy: number
    attempts_count: number
    recommendations?: string[]
  }>
  strong_topics?: Array<{
    topic: string
    accuracy: number
    attempts_count: number
  }>
  study_schedule?: Array<{
    day: number
    focus: string
    activities?: string[]
    estimated_time?: string
  }>
  overall_performance?: {
    total_attempts?: number
    accuracy?: number
    improvement_trend?: string
  }
}

export const StudyPlanView = ({ plan }: StudyPlanViewProps) => {
  const content = plan.plan_content as PlanContent

  return (
    <div className="flex flex-col gap-6">
      {plan.description && (
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{plan.description}</p>
          </CardContent>
        </Card>
      )}

      {content.overall_performance && (
        <Card>
          <CardHeader>
            <CardTitle>Overall Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Attempts</p>
                <p className="text-2xl font-bold">
                  {content.overall_performance.total_attempts ?? 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Overall Accuracy</p>
                <p className="text-2xl font-bold">
                  {content.overall_performance.accuracy?.toFixed(1) ?? 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {content.weak_topics && content.weak_topics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Topics to Focus On</CardTitle>
            <CardDescription>
              These topics need more practice based on your performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {content.weak_topics.map((topic, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">{topic.topic}</h4>
                    <Badge variant="destructive">
                      {topic.accuracy.toFixed(1)}% accuracy
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {topic.attempts_count} attempts
                  </p>
                  {topic.recommendations && topic.recommendations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium mb-1">Recommendations:</p>
                      <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                        {topic.recommendations.map((rec, recIndex) => (
                          <li key={recIndex}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {content.strong_topics && content.strong_topics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Strong Topics</CardTitle>
            <CardDescription>
              You're doing well in these areas
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {content.strong_topics.map((topic, index) => (
                <Badge key={index} variant="secondary" className="text-sm">
                  {topic.topic} ({topic.accuracy.toFixed(1)}%)
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {content.study_schedule && content.study_schedule.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>7-Day Study Schedule</CardTitle>
            <CardDescription>
              Recommended daily activities to improve your performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {content.study_schedule.map((day, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Day {day.day}</h4>
                    {day.estimated_time && (
                      <Badge variant="outline">{day.estimated_time}</Badge>
                    )}
                  </div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Focus: {day.focus}
                  </p>
                  {day.activities && day.activities.length > 0 && (
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {day.activities.map((activity, actIndex) => (
                        <li key={actIndex}>{activity}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

