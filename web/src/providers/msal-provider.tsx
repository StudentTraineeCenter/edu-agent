import { PublicClientApplication } from '@azure/msal-browser'
import { MsalProvider } from '@azure/msal-react'
import { msalConfig } from '@/lib/msal-config'
import { useEffect } from 'react'

const msalInstance = new PublicClientApplication(msalConfig)

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
