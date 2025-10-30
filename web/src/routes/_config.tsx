import {
  createRootRoute,
  createRoute,
  Outlet,
  redirect,
} from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { ProjectDetailPage } from './project-detail-route'
import { IndexPage } from './home-route'
import { ProjectListPage } from './project-list-route'
import { ChatDetailPage } from './chat-detail-route'
import { DocumentDetailPage } from './document-detail-route'
import { QuizDetailPage } from './quiz-detail-route'
import { FlashcardDetailPage } from './flashcard-detail-route'
import { z } from 'zod'
import { MessageSquareIcon } from 'lucide-react'
import { ConversationEmptyState } from '@/components/ai-elements/conversation'

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
      <Outlet />
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

export const projectIndexRoute = createRoute({
  path: '/',
  getParentRoute: () => projectDetailRoute,
  component: () => (
    <div className="flex flex-1 items-center justify-center">
      <ConversationEmptyState
        icon={<MessageSquareIcon className="size-8" />}
        title="Select a chat"
        description="Choose a chat from the sidebar to start a conversation."
      />
    </div>
  ),
})

export const chatDetailRoute = createRoute({
  path: '/chats/$chatId',
  getParentRoute: () => projectDetailRoute,
  component: ChatDetailPage,
})

export const documentDetailRoute = createRoute({
  path: '/documents/$documentId',
  getParentRoute: () => projectDetailRoute,
  component: DocumentDetailPage,
})

export const flashcardDetailRoute = createRoute({
  path: '/flashcards/$flashcardGroupId',
  getParentRoute: () => projectDetailRoute,
  component: FlashcardDetailPage,
})

export const quizDetailRoute = createRoute({
  path: '/quizzes/$quizId',
  getParentRoute: () => projectDetailRoute,
  component: QuizDetailPage,
})

export const routeTree = rootRoute.addChildren([
  projectsRoute,
  projectDetailRoute.addChildren([
    projectIndexRoute,
    chatDetailRoute,
    documentDetailRoute,
    flashcardDetailRoute,
    quizDetailRoute,
  ]),
  indexRoute,
])
