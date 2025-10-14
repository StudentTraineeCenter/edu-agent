import createClient from 'openapi-fetch'
import type { components, paths } from './types'
import { env } from '@/env'

export const baseUrl = env.VITE_SERVER_URL

// Create a client factory that accepts a token
export const createApiClient = (token?: string) => {
  return createClient<paths>({
    baseUrl,
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  })
}

// Default client without auth (for public endpoints)
const client = createApiClient()

export default client

export type Schema = components['schemas']

export type Project = Schema['ProjectDto']
export type Chat = Schema['ChatDto']
export type ChatMessage = Schema['ChatMessageDto']
export type Document = Schema['DocumentDto']
export type User = Schema['UserDto']
export type Source = Schema['SourceDto']

export type ChatCreateRequest = Schema['ChatCreateRequest']
