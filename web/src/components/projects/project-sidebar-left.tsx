import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import { ProjectChatList } from './project-chat-list'
import { ProjectDocumentList } from './project-document-list'
import { currentProjectIdAtom, projectAtom } from '@/data-acess/project'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Loader2Icon } from 'lucide-react'

type Props = React.ComponentProps<typeof Sidebar>

export function ProjectSidebarLeft({ ...props }: Props) {
  const currentProjectId = useAtomValue(currentProjectIdAtom)
  const projectResult = useAtomValue(projectAtom(currentProjectId ?? ''))

  return (
    <Sidebar className="border-r-0" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            {Result.builder(projectResult)
              .onInitialOrWaiting(() => (
                <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
                  <Loader2Icon className="size-4 animate-spin" />
                  <span>Loading project...</span>
                </div>
              ))
              .onFailure(() => (
                <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
                  <span>Failed to load project</span>
                </div>
              ))
              .onSuccess((project) => (
                <span className="text-lg font-bold">{project.name}</span>
              ))
              .render()}
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <ProjectChatList />
        <ProjectDocumentList />
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
