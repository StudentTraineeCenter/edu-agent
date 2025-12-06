import { Button } from '@/components/ui/button'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { flashcardDetailStateAtom, setModeAtom, type FlashcardMode } from '@/data-acess/flashcard-detail-state'
import { Option } from 'effect'
import { CheckCircle2 } from 'lucide-react'

type FlashcardModeSelectorProps = {
  flashcardGroupId: string
}

export const FlashcardModeSelector = ({
  flashcardGroupId,
}: FlashcardModeSelectorProps) => {
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const setMode = useAtomSet(setModeAtom)

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const currentMode = state?.mode ?? 'normal'
  const hasStarted = state && (state.markedCardIds.size > 0 || state.isCompleted)

  // Don't show selector if already started
  if (hasStarted) return null

  const modes: Array<{ value: FlashcardMode; label: string; description: string }> = [
    {
      value: 'normal',
      label: 'Normal',
      description: 'Go through all flashcards once',
    },
    {
      value: 'cycle-until-correct',
      label: 'Cycle Until Correct',
      description: 'Keep practicing wrong cards until all are correct',
    },
  ]

  return (
    <div className="flex flex-col gap-4 p-6 border rounded-lg bg-card">
      <div>
        <h3 className="text-lg font-semibold mb-1">Practice Mode</h3>
        <p className="text-sm text-muted-foreground">
          Choose how you want to practice these flashcards
        </p>
      </div>
      <div className="flex gap-3">
        {modes.map((mode) => (
          <Button
            key={mode.value}
            variant={currentMode === mode.value ? 'default' : 'outline'}
            className="flex-1 flex flex-col items-start h-auto py-4 px-4"
            onClick={() => setMode({ flashcardGroupId, mode: mode.value })}
          >
            <div className="flex items-center gap-2 w-full mb-1">
              {currentMode === mode.value && (
                <CheckCircle2 className="h-4 w-4" />
              )}
              <span className="font-semibold">{mode.label}</span>
            </div>
            <span className="text-xs text-muted-foreground text-left">
              {mode.description}
            </span>
          </Button>
        ))}
      </div>
    </div>
  )
}

