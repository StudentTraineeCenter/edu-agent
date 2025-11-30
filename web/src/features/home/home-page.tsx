import { useAuth } from '@/hooks/use-auth'
import { UserProfile } from '@/components/auth/user-profile'
import { LoginButton } from '@/components/auth/login-button'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { useEffect } from 'react'

export const HomePage = () => {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const search = useSearch({ from: '/' })

  // Handle redirect after successful login
  useEffect(() => {
    if (isAuthenticated) {
      const redirectUrl =
        search?.redirect || sessionStorage.getItem('auth.redirect')
      if (redirectUrl) {
        sessionStorage.removeItem('auth.redirect')
        // Ensure redirect URLs are prefixed with /dashboard
        const dashboardUrl = redirectUrl.startsWith('/dashboard')
          ? redirectUrl
          : `/dashboard${redirectUrl}`
        navigate({ to: dashboardUrl })
      } else {
        // Default redirect to dashboard
        navigate({ to: '/dashboard' })
      }
    }
  }, [isAuthenticated, navigate, search?.redirect])

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-4">
        <div className="lg:col-span-1">
          {isAuthenticated ? <UserProfile /> : <LoginButton />}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 items-start">
          <div className="lg:col-span-2">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              EduAgent
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              An AI‑powered study copilot to organize materials, chat with your
              content, and accelerate learning.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
