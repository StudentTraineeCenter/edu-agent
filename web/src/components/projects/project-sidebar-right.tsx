import { PlusIcon } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarSeparator,
} from '@/components/ui/sidebar'
import { NavMaterials } from '@/components/projects/nav-materials'
import { NavUser } from '@/components/projects/nav-user'
import { Button } from '@/components/ui/button'
import { useFlashcardGroupsQuery } from '@/data-acess/flashcard'
import { useQuizzesQuery } from '@/data-acess/quiz'
import type { Material } from '@/integrations/api'
import { useMemo } from 'react'

type Props = React.ComponentProps<typeof Sidebar> & {
  projectId: string
  onCreateFlashcard?: () => void
  onCreateQuiz?: () => void
  onSelectMaterialId?: (materialId: string) => void
}

export function ProjectSidebarRight({
  projectId,
  onCreateFlashcard,
  onCreateQuiz,
  onSelectMaterialId,
  ...props
}: Props) {
  const flashcardGroupsQuery = useFlashcardGroupsQuery(projectId)
  const flashcardGroups = flashcardGroupsQuery.data?.data ?? []

  const quizzesQuery = useQuizzesQuery(projectId)
  const quizzes = quizzesQuery.data?.data ?? []

  const materials = useMemo(() => {
    return [
      ...(flashcardGroups.map((group) => ({
        type: 'flashcard_group' as const,
        ...group,
      })) ?? []),
      ...(quizzes.map((quiz) => ({
        type: 'quiz' as const,
        ...quiz,
      })) ?? []),
    ] as Material[]
  }, [flashcardGroups, quizzes])


  return (
    <Sidebar
      collapsible="none"
      className="sticky top-0 hidden h-svh border-l lg:flex !w-[26rem]"
      {...props}
    >
      <SidebarHeader className="border-sidebar-border border-b h-30">
        <div className="flex items-stretch gap-2 h-full">
          <Button
            variant="outline"
            className="flex-1 flex flex-col items-center justify-center gap-1 h-full"
            onClick={onCreateFlashcard}
          >
            <PlusIcon className="size-4" />
            <span className="text-sm">Flashcard</span>
          </Button>
          <Button
            variant="outline"
            className="flex-1 flex flex-col items-center justify-center gap-1 h-full"
            onClick={onCreateQuiz}
          >
            <PlusIcon className="size-4" />
            <span className="text-sm">Quiz</span>
          </Button>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMaterials
          materials={materials}
          onSelectMaterialId={onSelectMaterialId}
        />
        <SidebarSeparator className="mx-0" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
