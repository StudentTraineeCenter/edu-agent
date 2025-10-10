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

type Props = React.ComponentProps<typeof Sidebar> & {
  materials: unknown[]
}

export function ProjectSidebarRight({ materials, ...props }: Props) {
  return (
    <Sidebar
      collapsible="none"
      className="sticky top-0 hidden h-svh border-l lg:flex"
      {...props}
    >
      <SidebarHeader className="border-sidebar-border border-b h-30">
        <div className="flex items-stretch gap-2 h-full">
          <Button
            variant="outline"
            className="flex-1 flex flex-col items-center justify-center gap-1 h-full"
          >
            <PlusIcon className="size-4" />
            <span className="text-sm">Flashcard</span>
          </Button>
          <Button
            variant="outline"
            className="flex-1 flex flex-col items-center justify-center gap-1 h-full"
          >
            <PlusIcon className="size-4" />
            <span className="text-sm">Quiz</span>
          </Button>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMaterials materials={materials} />
        <SidebarSeparator className="mx-0" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
