import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Skeleton } from '@/components/ui/skeleton'
import { FlashcardDetail } from '@/components/flashcards/flashcard-detail'
import { flashcardGroupAtom } from '@/data-acess/flashcard'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { flashcardDetailRoute } from '@/routes/_config'

const FlashcardHeader = ({ title }: { title?: string }) => (
  <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2">
    <div className="flex flex-1 items-center gap-2 px-3">
      <SidebarTrigger />
      <Separator
        orientation="vertical"
        className="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1">{title}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  </header>
)

export const FlashcardDetailPage = () => {
  const { flashcardGroupId } = flashcardDetailRoute.useParams()
  const groupResult = useAtomValue(flashcardGroupAtom(flashcardGroupId))

  return (
    <>
      {Result.builder(groupResult)
        .onSuccess((res) => (
          <FlashcardHeader title={res.flashcard_group?.name || 'Flashcards'} />
        ))
        .onInitialOrWaiting(() => (
          <div className="h-14">
            <Skeleton className="w-72 h-7 mt-3 ml-4" />
          </div>
        ))
        .onFailure(() => <FlashcardHeader title="Flashcards" />)
        .render()}

      <div className="flex flex-1 flex-col p-4">
        <div className="max-w-5xl mx-auto w-full flex flex-col rounded-lg border h-[calc(100vh-6rem)] p-4 overflow-auto">
          <FlashcardDetail
            flashcardGroupId={flashcardGroupId}
            className="flex-1"
          />
        </div>
      </div>
    </>
  )
}
