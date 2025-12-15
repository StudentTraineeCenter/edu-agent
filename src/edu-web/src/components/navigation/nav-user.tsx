import {
  Brain,
  ChevronsUpDown,
  FileText,
  HelpCircle,
  LogOutIcon,
  MessageSquare,
} from 'lucide-react'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { currentUserAtom, signOutAtom } from '@/data-acess/auth'
import { usageAtom } from '@/data-acess/usage'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { useNavigate } from '@tanstack/react-router'

const UsageSection = () => {
  const usageResult = useAtomValue(usageAtom)

  return Result.builder(usageResult)
    .onFailure(() => <div>Failed to load usage data.</div>)
    .onSuccess((usage) => (
      <>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">Chat Messages</span>
          </div>
          <span className="text-xs font-medium">
            {usage.chat_messages.used} / {usage.chat_messages.limit}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">Flashcards</span>
          </div>
          <span className="text-xs font-medium">
            {usage.flashcard_generations.used} /{' '}
            {usage.flashcard_generations.limit}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">Mind Maps</span>
          </div>
          <span className="text-xs font-medium">
            {usage.mindmap_generations.used} / {usage.mindmap_generations.limit}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">Quizzes</span>
          </div>
          <span className="text-xs font-medium">
            {usage.quiz_generations.used} / {usage.quiz_generations.limit}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">Documents</span>
          </div>
          <span className="text-xs font-medium">
            {usage.document_uploads.used} / {usage.document_uploads.limit}
          </span>
        </div>
      </>
    ))
    .render()
}

export function NavUser() {
  const { isMobile } = useSidebar()
  const navigate = useNavigate()

  const currentUserResult = useAtomValue(currentUserAtom)

  const signOut = useAtomSet(signOutAtom)

  const handleSignOut = () => {
    signOut()
    navigate({ to: '/sign-in' })
  }

  return Result.builder(currentUserResult)
    .onFailure(() => <div>Failed to load user data.</div>)
    .onSuccess(({ name, initials, email }) => {
      return (
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage src={undefined} alt={name} />
                    <AvatarFallback className="rounded-lg">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{name}</span>
                    <span className="truncate text-xs">{email}</span>
                  </div>
                  <ChevronsUpDown className="ml-auto size-4" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                side={isMobile ? 'bottom' : 'right'}
                align="end"
                sideOffset={4}
              >
                <DropdownMenuLabel className="p-0 font-normal">
                  <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                    <Avatar className="h-8 w-8 rounded-lg">
                      <AvatarImage src={undefined} alt={name} />
                      <AvatarFallback className="rounded-lg">
                        {initials}
                      </AvatarFallback>
                    </Avatar>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-medium">{name}</span>
                      <span className="truncate text-xs">{email}</span>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuLabel className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                  Usage Today
                </DropdownMenuLabel>
                <div className="px-2 py-1.5 space-y-2">
                  <UsageSection />
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut}>
                  <LogOutIcon />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      )
    })
    .render()
}
