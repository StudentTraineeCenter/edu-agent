import { useEffect, useRef, useMemo } from 'react'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import { Result } from '@effect-atom/atom-react'
import { documentsAtom, refreshDocumentsAtom } from '@/data-acess/document'

const POLL_INTERVAL_MS = 3000 // Poll every 3 seconds

/**
 * Hook that automatically polls for document status updates when there are
 * documents that are not yet ready (status !== 'indexed' && status !== 'failed')
 */
export const useDocumentPolling = (projectId: string) => {
  const documentsResult = useAtomValue(documentsAtom(projectId))
  const refreshDocuments = useAtomSet(refreshDocumentsAtom, {
    mode: 'promise',
  })
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Check if there are unready documents
  const hasUnreadyDocuments = useMemo(() => {
    if (Result.isSuccess(documentsResult)) {
      return documentsResult.value.some(
        (doc) => doc.status !== 'indexed' && doc.status !== 'failed',
      )
    }
    return false
  }, [documentsResult])

  useEffect(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    // Only poll if we have unready documents
    if (hasUnreadyDocuments) {
      // Start polling
      intervalRef.current = setInterval(() => {
        refreshDocuments(projectId)
      }, POLL_INTERVAL_MS)
    }

    // Cleanup on unmount or when dependencies change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [hasUnreadyDocuments, projectId, refreshDocuments])
}
