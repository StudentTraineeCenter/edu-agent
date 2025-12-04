import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'

import { routeTree } from './routes/_config.tsx'

import * as TanStackQueryProvider from './integrations/tanstack-query/root-provider.tsx'
import { SupabaseProvider } from './providers/supabase-provider.tsx'

import './styles.css'
import reportWebVitals from './reportWebVitals.ts'
import { TooltipProvider } from '@/components/ui/tooltip.tsx'
import { ModalProvider } from '@/providers/modal-provider.tsx'
import { ThemeProvider } from '@/providers/theme-provider.tsx'

const TanStackQueryProviderContext = TanStackQueryProvider.getContext()
const router = createRouter({
  routeTree: routeTree,
  context: {
    ...TanStackQueryProviderContext,
  },
  defaultPreload: 'intent',
  scrollRestoration: true,
  defaultStructuralSharing: true,
  defaultPreloadStaleTime: 0,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const rootElement = document.getElementById('app')
if (rootElement && !rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <StrictMode>
      <ThemeProvider>
        <SupabaseProvider>
          <TanStackQueryProvider.Provider {...TanStackQueryProviderContext}>
            <TooltipProvider>
              <ModalProvider>
                <RouterProvider router={router} />
              </ModalProvider>
            </TooltipProvider>
          </TanStackQueryProvider.Provider>
        </SupabaseProvider>
      </ThemeProvider>
    </StrictMode>,
  )
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals()
