import { createRootRoute, createRoute, redirect } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { AppShell } from './_app-shell'
import { ProjectDetailPage } from './project-detail-route'
import { IndexPage } from './home-route'
import { ProjectListPage } from './project-list-route'
import { ChatDetailPage } from './chat-detail-route'
import { DocumentDetailPage } from './document-detail-route'
import { QuizDetailPage } from './quiz-detail-route'
import { FlashcardDetailPage } from './flashcard-detail-route'
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
  component: IndexPage,
})

export const projectsRoute = createRoute({
  path: '/projects',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: ProjectListPage,
})

export const projectDetailRoute = createRoute({
  path: '/projects/$projectId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: ProjectDetailPage,
})

export const chatDetailRoute = createRoute({
  path: '/projects/$projectId/chats/$chatId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: ChatDetailPage,
})

export const documentDetailRoute = createRoute({
  path: '/projects/$projectId/documents/$documentId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: DocumentDetailPage,
})

export const flashcardDetailRoute = createRoute({
  path: '/projects/$projectId/flashcards/$flashcardGroupId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: FlashcardDetailPage,
})

export const quizDetailRoute = createRoute({
  path: '/projects/$projectId/quizzes/$quizId',
  getParentRoute: () => rootRoute,
  beforeLoad: requireAuth,
  component: QuizDetailPage,
})

export const routeTree = rootRoute.addChildren([
  projectsRoute,
  projectDetailRoute,
  chatDetailRoute,
  documentDetailRoute,
  flashcardDetailRoute,
  quizDetailRoute,
  indexRoute,
])
