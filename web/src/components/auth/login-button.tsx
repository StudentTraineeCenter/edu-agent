import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'
import { LogIn } from 'lucide-react'
import { useSearch } from '@tanstack/react-router'

export const LoginButton = () => {
  const { login, isLoading } = useAuth()
  const search = useSearch({ from: '/' })

  const handleLogin = () => {
    // Store the redirect URL before login
    if (search?.redirect) {
      sessionStorage.setItem('auth.redirect', search.redirect)
    }
    login()
  }

  return (
    <Button
      onClick={handleLogin}
      disabled={isLoading}
      className="flex items-center gap-2"
    >
      <LogIn className="h-4 w-4" />
      {isLoading ? 'Signing in...' : 'Sign in with Microsoft'}
    </Button>
  )
}
