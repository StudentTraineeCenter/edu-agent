import { LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'

export const LogoutButton = () => {
  const { logout, isLoading } = useAuth()

  const handleLogout = () => {
    logout()
  }

  return (
    <Button
      variant="outline"
      onClick={handleLogout}
      disabled={isLoading}
      className="flex items-center gap-2"
    >
      <LogOut className="h-4 w-4" />
      {isLoading ? 'Signing out...' : 'Sign out'}
    </Button>
  )
}
