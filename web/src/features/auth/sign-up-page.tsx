import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Link, useNavigate, useSearch } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const SignUpPage = () => {
  const { signUp, isLoading, signUpError, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const search = useSearch({ from: '/sign-up' })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [hasSubmitted, setHasSubmitted] = useState(false)

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !hasSubmitted) {
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
  }, [isAuthenticated, navigate, search?.redirect, hasSubmitted])

  // Update error when signUpError changes
  useEffect(() => {
    if (signUpError) {
      setError(
        signUpError instanceof Error
          ? signUpError.message
          : 'Sign up failed. Please try again.',
      )
      setHasSubmitted(false)
    }
  }, [signUpError])

  // Handle successful sign-up (might need email confirmation)
  useEffect(() => {
    if (hasSubmitted && !isLoading && !signUpError) {
      // Sign-up completed successfully
      if (isAuthenticated) {
        // User is authenticated immediately (no email confirmation required)
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
      } else {
        // Email confirmation required
        setSuccess(true)
      }
    }
  }, [
    hasSubmitted,
    isLoading,
    signUpError,
    isAuthenticated,
    navigate,
    search?.redirect,
  ])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setHasSubmitted(false)

    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long')
      return
    }

    // Store the redirect URL before sign up
    if (search?.redirect) {
      sessionStorage.setItem('auth.redirect', search.redirect)
    }

    setHasSubmitted(true)
    signUp({ email, password })
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Check your email
            </h1>
            <p className="text-sm text-muted-foreground">
              We've sent a confirmation link to <strong>{email}</strong>
            </p>
            <p className="text-sm text-muted-foreground">
              Please click the link in the email to verify your account and
              complete sign up.
            </p>
            <div className="pt-4">
              <Link
                to="/sign-in"
                className="text-sm text-primary hover:underline"
              >
                Back to sign in
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Create an account
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Enter your email and password to create your account
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
              placeholder="At least 6 characters"
              autoComplete="new-password"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Confirm your password"
              autoComplete="new-password"
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !email || !password || !confirmPassword}
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </Button>

          <div className="text-center text-xs text-muted-foreground">
            By creating an account, you agree to our{' '}
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
            Already have an account?{' '}
            <Link
              to="/sign-in"
              search={
                search?.redirect ? { redirect: search.redirect } : undefined
              }
              className="text-primary hover:underline"
            >
              Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
