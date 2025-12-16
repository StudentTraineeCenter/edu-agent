import { Result, useAtomValue } from '@effect-atom/atom-react'
import { ArrowLeft } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { useMemo } from 'react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { chatAtom } from '@/data-acess/chat'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'

const ChatHeaderContent = (props: { projectId: string; chatId: string }) => {
  const { projectId, chatId } = props
  const atomInput = useMemo(() => `${projectId}:${chatId}`, [projectId, chatId])
  const chatResult = useAtomValue(chatAtom(atomInput))

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

export const ChatHeader = (props: ChatHeaderProps) => {
  const { projectId, chatId } = props

  return (
    <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        <SidebarTrigger />
        <Button variant="ghost" size="icon" className="size-7" asChild>
          <Link to="/dashboard/p/$projectId" params={{ projectId }}>
            <ArrowLeft className="size-4" />
            <span className="sr-only">Back to project</span>
          </Link>
        </Button>
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <ChatHeaderContent projectId={projectId} chatId={chatId} />
      </div>
    </header>
  )
}
