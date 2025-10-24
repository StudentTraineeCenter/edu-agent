import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
} from '@/components/ui/sidebar'
import {
  MoreHorizontal,
  BrainCircuit,
  ListChecks,
  PlayIcon,
  Loader2Icon,
} from 'lucide-react'
import { truncate } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Material, materialsAtom } from '@/data-acess/materials'
import type { FlashcardGroupDto, QuizDto } from '@/integrations/api/client'
import { currentProjectIdAtom } from '@/data-acess/project'
import { useNavigate } from '@tanstack/react-router'

type Props = React.ComponentProps<typeof SidebarGroup>

const FlashcardGroupItem = ({
  flashcardGroup,
}: {
  flashcardGroup: FlashcardGroupDto
}) => {
  const navigate = useNavigate()
  const currentProjectId = useAtomValue(currentProjectIdAtom)

  const handleSelect = () => {
    if (!currentProjectId) return

    navigate({
      to: '/projects/$projectId/flashcards/$flashcardGroupId',
      params: {
        projectId: currentProjectId,
        flashcardGroupId: flashcardGroup.id,
      },
    })
  }

  return (
    <SidebarMenuItem key={flashcardGroup.id}>
      <SidebarMenuButton tooltip={flashcardGroup.name} onClick={handleSelect}>
        <BrainCircuit className="size-4" />
        {truncate(flashcardGroup.name, 30)}
      </SidebarMenuButton>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <SidebarMenuAction>
            <MoreHorizontal />
          </SidebarMenuAction>
        </DropdownMenuTrigger>
        <DropdownMenuContent side="right" align="start">
          <DropdownMenuItem onClick={() => {}}>
            <PlayIcon className="size-4 mr-2" />
            <span>Study</span>
          </DropdownMenuItem>
          <DropdownMenuItem variant="destructive" onClick={() => {}}>
            <span>Delete</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  )
}

const QuizItem = ({ quiz }: { quiz: QuizDto }) => {
  const currentProjectId = useAtomValue(currentProjectIdAtom)
  const navigate = useNavigate()

  const handleSelect = () => {
    if (!currentProjectId) return

    navigate({
      to: '/projects/$projectId/quizzes/$quizId',
      params: {
        projectId: currentProjectId,
        quizId: quiz.id,
      },
    })
  }

  return (
    <SidebarMenuItem key={quiz.id}>
      <SidebarMenuButton tooltip={quiz.name} onClick={handleSelect}>
        <ListChecks className="size-4" />
        {truncate(quiz.name, 30)}
      </SidebarMenuButton>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <SidebarMenuAction>
            <MoreHorizontal />
          </SidebarMenuAction>
        </DropdownMenuTrigger>
        <DropdownMenuContent side="right" align="start">
          <DropdownMenuItem onClick={() => {}}>
            <PlayIcon className="size-4 mr-2" />
            <span>Study</span>
          </DropdownMenuItem>
          <DropdownMenuItem variant="destructive" onClick={() => {}}>
            <span>Delete</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  )
}

export const NavMaterials = ({ ...props }: Props) => {
  const currentProjectId = useAtomValue(currentProjectIdAtom)
  const materialsResult = useAtomValue(materialsAtom(currentProjectId ?? ''))

  console.log(materialsResult)

  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>Materials</SidebarGroupLabel>

      <SidebarGroupContent>
        <SidebarMenu>
          {Result.builder(materialsResult)
            .onInitialOrWaiting(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
                <Loader2Icon className="size-4 animate-spin" />
                <span>Loading materials...</span>
              </div>
            ))
            .onDefect(() => (
              <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
                <span>Failed to load materials</span>
              </div>
            ))
            .onSuccess((materials) => {
              return materials.map((material) => {
                return Material.$match(material, {
                  FlashcardGroup: ({ data: flashcardGroup }) => {
                    return (
                      <FlashcardGroupItem
                        key={flashcardGroup.id}
                        flashcardGroup={flashcardGroup}
                      />
                    )
                  },
                  Quiz: ({ data: quiz }) => {
                    return <QuizItem key={quiz.id} quiz={quiz} />
                  },
                })
              })
            })
            .render()}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
