import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue } from '@effect-atom/atom-react'
import { quizAtom } from '@/data-acess/quiz'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'

const QuizHeaderContent = ({ quizId }: { quizId: string }) => {
  const quizResult = useAtomValue(quizAtom(quizId))

  return Result.builder(quizResult)
    .onSuccess((quiz) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {quiz.quiz?.name ?? 'Quiz'}
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
              Quiz
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

type QuizHeaderProps = {
  quizId: string
}

export const QuizHeader = ({ quizId }: QuizHeaderProps) => {
  const quizResult = useAtomValue(quizAtom(quizId))

  return (
    <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(quizResult) && <SidebarTrigger />}
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <QuizHeaderContent quizId={quizId} />
      </div>
    </header>
  )
}
