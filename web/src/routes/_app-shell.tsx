import { Outlet, useLocation } from '@tanstack/react-router'
import { AppSidebar } from '@/components/navigation/app-sidebar'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { useAuth } from '@/hooks/use-auth'

export const AppShell = () => {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  // Only show sidebar on dashboard routes
  const isDashboardRoute = location.pathname.startsWith('/dashboard')

  if (!isAuthenticated || !isDashboardRoute) {
    return <Outlet />
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        {/* <div className="flex h-12 items-center gap-2 border-b px-2">
          <SidebarTrigger />
          <div className="text-sm font-semibold">EduAgent</div>
        </div> */}
        <div className="min-h-0 flex-1 overflow-auto">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
