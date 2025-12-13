import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'
import { LogIn } from 'lucide-react'
import { useSearch } from '@tanstack/react-router'
import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export const LoginButton = () => {
  const { login, sendMagicLink, isLoading, loginError, magicLinkError } =
    useAuth()
  const search = useSearch({ from: '/' })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    // Store the redirect URL before login
    if (search?.redirect) {
      sessionStorage.setItem('auth.redirect', search.redirect)
    }
    login({ email, password })
  }

  const handleMagicLink = async () => {
    // Store the redirect URL before login
    if (search?.redirect) {
      sessionStorage.setItem('auth.redirect', search.redirect)
    }
    sendMagicLink(email)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="flex items-center gap-2">
          <LogIn className="h-4 w-4" />
          Sign in
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Sign in</DialogTitle>
          <DialogDescription>
            Sign in with your email and password, or use a magic link.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>
          {(loginError || magicLinkError) && (
            <p className="text-sm text-red-500">
              {loginError instanceof Error
                ? loginError.message
                : magicLinkError instanceof Error
                  ? magicLinkError.message
                  : 'Login failed'}
            </p>
          )}
          <div className="flex gap-2">
            <Button type="submit" disabled={isLoading || !email}>
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleMagicLink}
              disabled={isLoading || !email}
            >
              Send magic link
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
