import { createRootRoute, createRoute, redirect } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { lazy, Suspense } from 'react'
import { AppShell } from './_app-shell'
import { z } from 'zod'

// Dynamic imports for code-splitting
const ProjectDetailRoute = lazy(() =>
  import('./project-detail-route').then((m) => ({
    default: m.ProjectDetailRoute,
  })),
)
const HomePage = lazy(() =>
  import('@/features/home/home-page').then((m) => ({ default: m.HomePage })),
)
const ChatDetailRoute = lazy(() =>
  import('./chat-detail-route').then((m) => ({ default: m.ChatDetailRoute })),
)
const DocumentDetailRoute = lazy(() =>
  import('./document-detail-route').then((m) => ({
    default: m.DocumentDetailRoute,
  })),
)
const QuizDetailRoute = lazy(() =>
  import('./quiz-detail-route').then((m) => ({ default: m.QuizDetailRoute })),
)
const FlashcardDetailRoute = lazy(() =>
  import('./flashcard-detail-route').then((m) => ({
    default: m.FlashcardDetailRoute,
  })),
)
const SettingsPage = lazy(() =>
  import('@/features/settings/settings-page').then((m) => ({
    default: m.SettingsPage,
  })),
)
const DashboardRoute = lazy(() =>
  import('./dashboard-route').then((m) => ({ default: m.DashboardRoute })),
)
const DashboardPage = lazy(() =>
  import('@/features/dashboard/dashboard-page').then((m) => ({
    default: m.DashboardPage,
  })),
)

const requireAuth = () => {
  // Check if user is authenticated by looking at MSAL keys in sessionStorage
  const msalKeys = Object.keys(sessionStorage).filter((key) =>
    key.startsWith('msal.'),
  )

  // Look for account keys specifically
  const accountKeys = msalKeys.filter((key) => key.includes('account'))
  const isAuthenticated = accountKeys.length > 0

  if (!isAuthenticated) {
    throw redirect({
      to: '/',
      search: {
        redirect: window.location.pathname,
      },
    })
  }
}

export const rootRoute = createRootRoute({
  component: () => (
    <>
      <AppShell />
      <TanStackRouterDevtools />
    </>
  ),
})

// Dashboard layout route - parent for all authenticated routes
export const dashboardRoute = createRoute({
  path: '/dashboard',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <DashboardRoute />
    </Suspense>
  ),
})

export const indexRoute = createRoute({
  path: '/',
  getParentRoute: () => rootRoute,
  validateSearch: z.object({ redirect: z.string().optional() }).optional(),
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <HomePage />
    </Suspense>
  ),
})

export const dashboardIndexRoute = createRoute({
  path: '/',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <DashboardPage />
    </Suspense>
  ),
})

export const projectDetailRoute = createRoute({
  path: '/p/$projectId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <ProjectDetailRoute />
    </Suspense>
  ),
})

export const chatDetailRoute = createRoute({
  path: '/p/$projectId/c/$chatId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <ChatDetailRoute />
    </Suspense>
  ),
})

export const documentDetailRoute = createRoute({
  path: '/p/$projectId/d/$documentId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <DocumentDetailRoute />
    </Suspense>
  ),
})

export const flashcardDetailRoute = createRoute({
  path: '/p/$projectId/f/$flashcardGroupId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <FlashcardDetailRoute />
    </Suspense>
  ),
})

export const quizDetailRoute = createRoute({
  path: '/p/$projectId/q/$quizId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <QuizDetailRoute />
    </Suspense>
  ),
})

export const settingsRoute = createRoute({
  path: '/settings',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          Loading...
        </div>
      }
    >
      <SettingsPage />
    </Suspense>
  ),
})

export const routeTree = rootRoute.addChildren([
  dashboardRoute.addChildren([
    dashboardIndexRoute,
    projectDetailRoute,
    chatDetailRoute,
    documentDetailRoute,
    flashcardDetailRoute,
    quizDetailRoute,
    settingsRoute,
  ]),
  indexRoute,
])
