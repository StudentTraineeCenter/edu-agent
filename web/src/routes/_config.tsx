import { createRootRoute, createRoute, redirect } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { AppShell } from './_app-shell'
import { ProjectDetailRoute } from './project-detail-route'
import { HomePage } from '@/features/home/home-page'
import { ChatDetailRoute } from './chat-detail-route'
import { DocumentDetailRoute } from './document-detail-route'
import { QuizDetailRoute } from './quiz-detail-route'
import { FlashcardDetailRoute } from './flashcard-detail-route'
import { SettingsPage } from '@/features/settings/settings-page'
import { DashboardRoute } from './dashboard-route'
import { DashboardPage } from '@/features/dashboard/dashboard-page'
import { z } from 'zod'

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
  component: DashboardRoute,
})

export const indexRoute = createRoute({
  path: '/',
  getParentRoute: () => rootRoute,
  validateSearch: z.object({ redirect: z.string().optional() }).optional(),
  component: HomePage,
})

export const dashboardIndexRoute = createRoute({
  path: '/',
  getParentRoute: () => dashboardRoute,
  component: () => <DashboardPage />,
})

export const projectDetailRoute = createRoute({
  path: '/p/$projectId',
  getParentRoute: () => dashboardRoute,
  component: ProjectDetailRoute,
})

export const chatDetailRoute = createRoute({
  path: '/p/$projectId/c/$chatId',
  getParentRoute: () => dashboardRoute,
  component: ChatDetailRoute,
})

export const documentDetailRoute = createRoute({
  path: '/p/$projectId/d/$documentId',
  getParentRoute: () => dashboardRoute,
  component: DocumentDetailRoute,
})

export const flashcardDetailRoute = createRoute({
  path: '/p/$projectId/f/$flashcardGroupId',
  getParentRoute: () => dashboardRoute,
  component: FlashcardDetailRoute,
})

export const quizDetailRoute = createRoute({
  path: '/p/$projectId/q/$quizId',
  getParentRoute: () => dashboardRoute,
  component: QuizDetailRoute,
})

export const settingsRoute = createRoute({
  path: '/settings',
  getParentRoute: () => dashboardRoute,
  component: SettingsPage,
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
