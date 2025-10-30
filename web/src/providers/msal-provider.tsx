import { msalInstance } from '@/lib/msal-service'
import { MsalProvider } from '@azure/msal-react'
import { useEffect } from 'react'

export const MSALProvider = ({ children }: { children: React.ReactNode }) => {
  useEffect(() => {
    const initializeMsal = async () => {
      try {
        await msalInstance.initialize()

        await msalInstance.handleRedirectPromise()

        msalInstance.getAllAccounts()
      } catch (error) {
        console.error('❌ MSAL initialization failed:', error)
      }
    }

    initializeMsal()
  }, [])

  return <MsalProvider instance={msalInstance}>{children}</MsalProvider>
}
