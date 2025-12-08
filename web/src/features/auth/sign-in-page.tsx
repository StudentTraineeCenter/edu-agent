import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Link, useNavigate, useSearch } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { useAtom, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { isAuthenticatedAtom, signInAtom } from '@/data-acess/auth'
import { Cause } from 'effect'

export const SignInPage = () => {
  const [signInResult, signIn] = useAtom(signInAtom)
  const isAuthenticated = useAtomValue(isAuthenticatedAtom)

  const isLoading = signInResult.waiting

  const navigate = useNavigate()
  const search = useSearch({ from: '/sign-in' })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  // const [error, setError] = useState<string | null>(null)

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const redirectUrl =
        search?.redirect || sessionStorage.getItem('auth.redirect')
      if (redirectUrl) {
        sessionStorage.removeItem('auth.redirect')
        const dashboardUrl = redirectUrl.startsWith('/dashboard')
          ? redirectUrl
          : `/dashboard${redirectUrl}`
        navigate({ to: dashboardUrl })
      } else {
        navigate({ to: '/dashboard' })
      }
    }
  }, [isAuthenticated, navigate, search?.redirect])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!email || !password) {
      // setError('Please enter both email and password')
      return
    }

    // Store the redirect URL before login
    if (search?.redirect) {
      sessionStorage.setItem('auth.redirect', search.redirect)
    }

    signIn({ type: 'password', email, password })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Sign in
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Enter your email and password to access your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
              autoComplete="email"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={isLoading}
            />
          </div>

          {signInResult._tag === 'Failure' && (
            <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive">
                {Cause.pretty(signInResult.cause)}
              </p>
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !email || !password}
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>

          <div className="text-center text-xs text-muted-foreground">
            By signing in, you agree to our{' '}
            <a
              href="https://github.com/StudentTraineeCenter/edu-agent/blob/master/docs/PRIVACY_POLICY.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Privacy Policy
            </a>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link
              to="/sign-up"
              search={
                search?.redirect ? { redirect: search.redirect } : undefined
              }
              className="text-primary hover:underline"
            >
              Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
