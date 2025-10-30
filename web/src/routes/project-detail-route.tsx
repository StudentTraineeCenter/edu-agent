import { ProjectSidebarLeft } from '@/components/projects/project-sidebar-left'
import { ProjectSidebarRight } from '@/components/projects/project-sidebar-right'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { currentProjectIdAtom } from '@/data-acess/project'
import { projectDetailRoute } from '@/routes/_config'
import { Outlet } from '@tanstack/react-router'
import { useAtomSet } from '@effect-atom/atom-react'
import { useEffect } from 'react'

const ProjectLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <SidebarProvider>
      <ProjectSidebarLeft />
      <SidebarInset>{children}</SidebarInset>
      <ProjectSidebarRight />
    </SidebarProvider>
  )
}

export const ProjectDetailPage = () => {
  const params = projectDetailRoute.useParams()
  const setCurrentProject = useAtomSet(currentProjectIdAtom)

  useEffect(() => {
    setCurrentProject(params.projectId)
  }, [params.projectId])

  return (
    <ProjectLayout>
      <Outlet />
    </ProjectLayout>
  )
}
