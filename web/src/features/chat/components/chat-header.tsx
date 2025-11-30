import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue } from '@effect-atom/atom-react'
import { chatAtom } from '@/data-acess/chat'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import { Link } from '@tanstack/react-router'

const ChatHeaderContent = ({ chatId }: { chatId: string }) => {
  const chatResult = useAtomValue(chatAtom(chatId))

  return Result.builder(chatResult)
    .onSuccess((chat) => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {chat.title ?? 'Untitled chat'}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .render()
}

type ChatHeaderProps = {
  chatId: string
  projectId: string
}

export const ChatHeader = ({ chatId, projectId }: ChatHeaderProps) => {
  const chatResult = useAtomValue(chatAtom(chatId))

  return (
    <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        {Result.isSuccess(chatResult) && (
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
        <ChatHeaderContent chatId={chatId} />
      </div>
    </header>
  )
}
