import { createRootRoute, createRoute, redirect } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { AppShell } from './_app-shell'
import { ProjectDetailRoute } from './project-detail-route'
import { HomePage } from '@/features/home/home-page'
import { ChatDetailRoute } from './chat-detail-route'
import { DocumentDetailRoute } from './document-detail-route'
import { QuizDetailRoute } from './quiz-detail-route'
import { FlashcardDetailRoute } from './flashcard-detail-route'
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

export const indexRoute = createRoute({
  path: '/',
  getParentRoute: () => rootRoute,
  validateSearch: z.object({ redirect: z.string().optional() }).optional(),
  component: HomePage,
})

export const projectDetailRoute = createRoute({
  path: '/p/$projectId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: ProjectDetailRoute,
})

export const chatDetailRoute = createRoute({
  path: '/p/$projectId/c/$chatId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: ChatDetailRoute,
})

export const documentDetailRoute = createRoute({
  path: '/p/$projectId/d/$documentId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: DocumentDetailRoute,
})

export const flashcardDetailRoute = createRoute({
  path: '/p/$projectId/f/$flashcardGroupId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: FlashcardDetailRoute,
})

export const quizDetailRoute = createRoute({
  path: '/p/$projectId/q/$quizId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: QuizDetailRoute,
})

export const routeTree = rootRoute.addChildren([
  projectDetailRoute,
  chatDetailRoute,
  documentDetailRoute,
  flashcardDetailRoute,
  quizDetailRoute,
  indexRoute,
])
