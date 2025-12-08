import { createRootRoute, createRoute, redirect } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { lazy, Suspense } from 'react'
import { AppShell } from '@/routes/_app-shell'
import { z } from 'zod'

const LoadingPage = () => {
  return (
    <div className="flex h-screen items-center justify-center">Loading...</div>
  )
}

// Dynamic imports for code-splitting
const ProjectDetailRoute = lazy(() =>
  import('./project-detail-route').then((m) => ({
    default: m.ProjectDetailRoute,
  })),
)
const HomePage = lazy(() =>
  import('@/features/home/home-page').then((m) => ({ default: m.HomePage })),
)
const SignInPage = lazy(() =>
  import('@/features/auth/sign-in-page').then((m) => ({
    default: m.SignInPage,
  })),
)
const SignUpPage = lazy(() =>
  import('@/features/auth/sign-up-page').then((m) => ({
    default: m.SignUpPage,
  })),
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
const NoteDetailRoute = lazy(() =>
  import('./note-detail-route').then((m) => ({
    default: m.NoteDetailRoute,
  })),
)
const MindMapDetailRoute = lazy(() =>
  import('./mind-map-detail-route').then((m) => ({
    default: m.MindMapDetailRoute,
  })),
)
const StudySessionDetailRoute = lazy(() =>
  import('./study-session-detail-route').then((m) => ({
    default: m.StudySessionDetailRoute,
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

const requireAuth = async () => {
  // Check if user is authenticated by checking Supabase session
  const { supabase } = await import('@/lib/supabase')

  const {
    data: { session },
  } = await supabase.auth.getSession()
  const isAuthenticated = !!session

  if (!isAuthenticated) {
    const isSignInPage = window.location.pathname === '/sign-in'

    throw redirect({
      to: '/sign-in',
      search: {
        redirect: isSignInPage ? undefined : window.location.pathname,
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
    <Suspense fallback={<LoadingPage />}>
      <DashboardRoute />
    </Suspense>
  ),
})

export const indexRoute = createRoute({
  path: '/',
  getParentRoute: () => rootRoute,
  validateSearch: z.object({ redirect: z.string().optional() }).optional(),
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <HomePage />
    </Suspense>
  ),
})

export const signInRoute = createRoute({
  path: '/sign-in',
  getParentRoute: () => rootRoute,
  validateSearch: z.object({ redirect: z.string().optional() }).optional(),
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <SignInPage />
    </Suspense>
  ),
})

export const signUpRoute = createRoute({
  path: '/sign-up',
  getParentRoute: () => rootRoute,
  validateSearch: z.object({ redirect: z.string().optional() }).optional(),
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <SignUpPage />
    </Suspense>
  ),
})

export const dashboardIndexRoute = createRoute({
  path: '/',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <DashboardPage />
    </Suspense>
  ),
})

export const projectDetailRoute = createRoute({
  path: '/p/$projectId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <ProjectDetailRoute />
    </Suspense>
  ),
})

export const chatDetailRoute = createRoute({
  path: '/p/$projectId/c/$chatId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <ChatDetailRoute />
    </Suspense>
  ),
})

export const documentDetailRoute = createRoute({
  path: '/p/$projectId/d/$documentId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <DocumentDetailRoute />
    </Suspense>
  ),
})

export const flashcardDetailRoute = createRoute({
  path: '/p/$projectId/f/$flashcardGroupId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <FlashcardDetailRoute />
    </Suspense>
  ),
})

export const quizDetailRoute = createRoute({
  path: '/p/$projectId/q/$quizId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <QuizDetailRoute />
    </Suspense>
  ),
})

export const noteDetailRoute = createRoute({
  path: '/p/$projectId/n/$noteId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <NoteDetailRoute />
    </Suspense>
  ),
})

export const mindMapDetailRoute = createRoute({
  path: '/p/$projectId/m/$mindMapId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <MindMapDetailRoute />
    </Suspense>
  ),
})

export const studySessionDetailRoute = createRoute({
  path: '/p/$projectId/study-session/$sessionId',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
      <StudySessionDetailRoute />
    </Suspense>
  ),
})

export const settingsRoute = createRoute({
  path: '/settings',
  getParentRoute: () => dashboardRoute,
  component: () => (
    <Suspense fallback={<LoadingPage />}>
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
    noteDetailRoute,
    mindMapDetailRoute,
    studySessionDetailRoute,
    settingsRoute,
  ]),
  indexRoute,
  signInRoute,
  signUpRoute,
])
