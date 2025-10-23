import { env } from '@/env'
import {
  type Configuration,
  LogLevel,
  type PopupRequest,
} from '@azure/msal-browser'

export const msalConfig: Configuration = {
  auth: {
    clientId: env.VITE_AZURE_ENTRA_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${env.VITE_AZURE_ENTRA_TENANT_ID}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      logLevel: LogLevel.Warning,
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return
        }
        switch (level) {
          case 0: // LogLevel.Error
            console.error(message)
            return
          case 1: // LogLevel.Warning
            console.warn(message)
            return
          case 2: // LogLevel.Info
            console.info(message)
            return
          case 3: // LogLevel.Verbose
            console.debug(message)
            return
        }
      },
    },
  },
}

export const loginRequest: PopupRequest = {
  scopes: ['User.Read'],
}

export const graphConfig = {
  graphMeEndpoint: 'https://graph.microsoft.com/v1.0/me',
  graphPhotoEndpoint: 'https://graph.microsoft.com/v1.0/me/photo/$value',
}
