import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { flashcardGroupAtom } from '@/data-acess/flashcard'
import {
  flashcardDetailStateAtom,
  setModeAtom,
  shuffleFlashcardsAtom,
  type FlashcardMode,
} from '@/data-acess/flashcard-detail-state'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Settings2, Shuffle } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Option } from 'effect'

type FlashcardHeaderContentProps = {
  flashcardGroupId: string
}

const FlashcardHeaderContent = ({
  flashcardGroupId,
}: FlashcardHeaderContentProps) => {
  const groupResult = useAtomValue(flashcardGroupAtom(flashcardGroupId))

  return Result.builder(groupResult)
    .onSuccess((res) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {res.flashcard_group?.name || 'Flashcards'}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .onFailure(() => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              Flashcards
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

type FlashcardHeaderProps = {
  flashcardGroupId: string
  projectId: string
}

export const FlashcardHeader = ({
  flashcardGroupId,
  projectId,
}: FlashcardHeaderProps) => {
  const groupResult = useAtomValue(flashcardGroupAtom(flashcardGroupId))
  const stateResult = useAtomValue(flashcardDetailStateAtom(flashcardGroupId))
  const setMode = useAtomSet(setModeAtom)
  const shuffleFlashcards = useAtomSet(shuffleFlashcardsAtom, {
    mode: 'promise',
  })

  const state = Option.isSome(stateResult) ? stateResult.value : null
  const currentMode = state?.mode ?? 'normal'

  const handleShuffle = async () => {
    await shuffleFlashcards({ flashcardGroupId })
  }

  const modes: Array<{ value: FlashcardMode; label: string }> = [
    {
      value: 'normal',
      label: 'Normal',
    },
    {
      value: 'cycle-until-correct',
      label: 'Cycle Until Correct',
    },
  ]

  return (
    <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(groupResult) && (
          <>
            <SidebarTrigger />
            <Button variant="ghost" size="icon" className="size-7" asChild>
              <Link to="/dashboard/p/$projectId" params={{ projectId }}>
                <ArrowLeft className="size-4" />
                <span className="sr-only">Back to project</span>
              </Link>
            </Button>
          </>
        )}
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <FlashcardHeaderContent flashcardGroupId={flashcardGroupId} />
      </div>
      <div className="flex items-center gap-2 px-3">
        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={handleShuffle}
          title="Shuffle flashcards"
        >
          <Shuffle className="h-4 w-4" />
          <span className="hidden sm:inline">Shuffle</span>
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2">
              <Settings2 className="h-4 w-4" />
              <span className="hidden sm:inline">
                {modes.find((m) => m.value === currentMode)?.label || 'Mode'}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Practice Mode</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuRadioGroup
              value={currentMode}
              onValueChange={(value) =>
                setMode({ flashcardGroupId, mode: value as FlashcardMode })
              }
            >
              {modes.map((mode) => (
                <DropdownMenuRadioItem key={mode.value} value={mode.value}>
                  {mode.label}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
