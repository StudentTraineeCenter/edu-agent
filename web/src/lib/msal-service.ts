import { PublicClientApplication } from '@azure/msal-browser'
import { msalConfig } from '@/lib/msal-config'
import { Effect } from 'effect'

export const msalInstance = new PublicClientApplication(msalConfig)

let isInitialized = false

// Initialize MSAL
export const initializeMsal = async () => {
  if (isInitialized) return

  await msalInstance.initialize()
  await msalInstance.handleRedirectPromise()
  isInitialized = true
}

// Helper functions
export const getAccessToken = async () => {
  await initializeMsal() // Auto-initialize if needed

  const accounts = msalInstance.getAllAccounts()
  if (accounts.length === 0) return null

  const response = await msalInstance.acquireTokenSilent({
    scopes: ['User.Read'],
    account: accounts[0],
  })
  return response.accessToken
}

export const getAccessTokenEffect = Effect.promise(() => getAccessToken())
