import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  CheckCircle,
  XCircle,
  Upload,
  RotateCcw,
  X,
  Trophy,
  ChevronDown,
  ArrowRight,
} from 'lucide-react'
import { useState } from 'react'
import type { FlashcardDto } from '@/integrations/api/client'
import { Result, useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import {
  answeredCardsAtom,
  flashcardDetailStateAtom,
  flashcardStatsAtom,
  startNewRoundAtom,
} from '@/data-acess/flashcard-detail-state'
import { Option } from 'effect'

type FlashcardCompletionScreenProps = {
  flashcardGroupId: string
  onSubmit: () => void
  onRetry: () => void
  onClose: () => void
}

type CompletionHeaderProps = {
  total: number
  round?: number
  mode?: 'normal' | 'cycle-until-correct'
}

const CompletionHeader = ({ total, round, mode }: CompletionHeaderProps) => {
  const isCycleMode = mode === 'cycle-until-correct'
  return (
    <div className="text-center space-y-2">
      <div className="flex items-center justify-center gap-2 mb-2">
        <Trophy className="h-8 w-8 text-yellow-500" />
        <h2 className="text-3xl font-bold">Round {round || 1} Complete!</h2>
      </div>
      <p className="text-muted-foreground">
        {isCycleMode && round && round > 1
          ? `You've completed ${total} flashcards in this round`
          : `You've completed all ${total} flashcards`}
      </p>
    </div>
  )
}

type StatCardProps = {
  icon?: React.ReactNode
  value: string | number
  label: string
  valueColor?: string
}

const StatCard = ({ icon, value, label, valueColor }: StatCardProps) => (
  <div className="flex flex-col items-center space-y-3 p-6 rounded-lg border bg-card">
    <div className={`flex items-center ${icon ? 'gap-2' : ''}`}>
      {icon}
      <div className={`text-4xl font-bold ${valueColor || ''}`}>{value}</div>
    </div>
    <div className="text-sm font-medium text-muted-foreground">{label}</div>
  </div>
)

const StatsGrid = ({ flashcardGroupId }: { flashcardGroupId: string }) => {
  const statsResult = useAtomValue(flashcardStatsAtom(flashcardGroupId))

  return Result.builder(statsResult)
    .onSuccess((stats) => {
      return (
        <div className="grid grid-cols-3 gap-6">
          <StatCard
            icon={<CheckCircle className="h-6 w-6 text-green-600" />}
            value={stats.correct}
            label="Correct"
            valueColor="text-green-600"
          />
          <StatCard
            icon={<XCircle className="h-6 w-6 text-red-600" />}
            value={stats.incorrect}
            label="Incorrect"
            valueColor="text-red-600"
          />
          <StatCard
            icon={null}
            value={`${stats.percentage}%`}
            label="Success Rate"
            valueColor="text-blue-600"
          />
        </div>
      )
    })
    .render()
}

type FlashcardListItemProps = {
  card: FlashcardDto
  index: number
}

const FlashcardListItem = ({ card, index }: FlashcardListItemProps) => (
  <div className="border-b last:border-0 pb-3 last:pb-0 space-y-2">
    <div className="flex items-start gap-2">
      <span className="text-xs font-medium text-muted-foreground w-6 shrink-0">
        {index + 1}
      </span>
      <div className="flex-1 space-y-1.5 min-w-0">
        <p className="text-sm font-medium">{card.question}</p>
        <p className="text-sm text-muted-foreground">{card.answer}</p>
      </div>
    </div>
  </div>
)

type FlashcardReviewSectionProps = {
  title: string
  cards: ReadonlyArray<FlashcardDto>
  icon: React.ReactNode
  isOpen: boolean
  onOpenChange: (open: boolean) => void
}

const FlashcardReviewSection = ({
  title,
  cards,
  icon,
  isOpen,
  onOpenChange,
}: FlashcardReviewSectionProps) => {
  if (cards.length === 0) return null

  return (
    <Collapsible open={isOpen} onOpenChange={onOpenChange}>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border bg-card p-4 hover:bg-accent transition-colors">
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-semibold">
            {title} ({cards.length})
          </span>
        </div>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-2">
        <div className="rounded-lg border bg-muted/50 p-4 space-y-3">
          {cards.map((card, idx) => (
            <FlashcardListItem key={card.id} card={card} index={idx} />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

type CompletionActionsProps = {
  flashcardGroupId: string
  total: number
  onSubmit: () => void
  onRetry: () => void
  onClose: () => void
}

const CompletionActions = ({
  flashcardGroupId,
  total,
  onSubmit,
  onRetry,
  onClose,
}: CompletionActionsProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const answeredCardsResult = useAtomValue(answeredCardsAtom(flashcardGroupId))
  const startNewRound = useAtomSet(startNewRoundAtom)

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const hasPendingPracticeRecords =
    Option.isSome(stateResult) &&
    Object.keys(stateResult.value.pendingPracticeRecords).length > 0

  const { incorrect } = Result.isSuccess(answeredCardsResult)
    ? answeredCardsResult.value
    : { incorrect: [] }

  const isCycleMode = state?.mode === 'cycle-until-correct'
  const hasWrongCards = incorrect.length > 0
  const canContinue = isCycleMode && hasWrongCards

  const handleContinueWithWrongCards = () => {
    if (!state) return
    const wrongCardIds = new Set(incorrect.map((card) => card.id))
    startNewRound({ flashcardGroupId, wrongCardIds })
  }

  return (
    <div className="flex flex-col gap-3">
      {canContinue && (
        <Button
          onClick={handleContinueWithWrongCards}
          variant="default"
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700"
          size="lg"
        >
          <ArrowRight className="h-4 w-4" />
          Continue with Wrong Cards ({incorrect.length})
        </Button>
      )}

      {hasPendingPracticeRecords && (
        <Button
          onClick={onSubmit}
          variant="default"
          className="w-full flex items-center justify-center gap-2"
          size="lg"
        >
          <Upload className="h-4 w-4" />
          Submit Practice Records ({total})
        </Button>
      )}

      <div className="flex gap-3">
        <Button
          onClick={onRetry}
          variant="outline"
          className="flex-1 flex items-center justify-center gap-2"
          size="lg"
        >
          <RotateCcw className="h-4 w-4" />
          Retry
        </Button>
        <Button
          onClick={onClose}
          variant="outline"
          className="flex-1 flex items-center justify-center gap-2"
          size="lg"
        >
          <X className="h-4 w-4" />
          Close
        </Button>
      </div>
    </div>
  )
}

export const FlashcardCompletionScreen = ({
  flashcardGroupId,
  onSubmit,
  onRetry,
  onClose,
}: FlashcardCompletionScreenProps) => {
  const [showCorrect, setShowCorrect] = useState(false)
  const [showIncorrect, setShowIncorrect] = useState(false)

  const answeredCardsResult = useAtomValue(answeredCardsAtom(flashcardGroupId))
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))

  const { correct, incorrect } = Result.isSuccess(answeredCardsResult)
    ? answeredCardsResult.value
    : { correct: [], incorrect: [] }

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const total = correct.length + incorrect.length

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-auto p-4">
      <div className="max-w-3xl mx-auto w-full space-y-8 py-8">
        <CompletionHeader
          total={total}
          round={state?.currentRound}
          mode={state?.mode}
        />

        <StatsGrid flashcardGroupId={flashcardGroupId} />

        <Separator />

        <div className="space-y-4">
          <FlashcardReviewSection
            title="Correct Answers"
            cards={correct}
            icon={<CheckCircle className="h-5 w-5 text-green-600" />}
            isOpen={showCorrect}
            onOpenChange={setShowCorrect}
          />

          <FlashcardReviewSection
            title="Incorrect Answers"
            cards={incorrect}
            icon={<XCircle className="h-5 w-5 text-red-600" />}
            isOpen={showIncorrect}
            onOpenChange={setShowIncorrect}
          />
        </div>

        <Separator />

        <CompletionActions
          total={total}
          onSubmit={onSubmit}
          onRetry={onRetry}
          onClose={onClose}
          flashcardGroupId={flashcardGroupId}
        />
      </div>
    </div>
  )
}
