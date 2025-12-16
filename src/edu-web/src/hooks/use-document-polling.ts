import { useEffect, useMemo, useRef } from 'react'
import { Result, useAtomSet, useAtomValue } from '@effect-atom/atom-react'
import { documentsAtom, refreshDocumentAtom } from '@/data-acess/document'

const POLL_INTERVAL_MS = 3000 // Poll every 3 seconds

/**
 * Hook that automatically polls for document status updates when there are
 * documents that are not yet ready (status !== 'indexed' && status !== 'failed')
 */
export const useDocumentPolling = (projectId: string) => {
  const documentsResult = useAtomValue(documentsAtom(projectId))
  const refreshDocument = useAtomSet(refreshDocumentAtom, {
    mode: 'promise',
  })
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Get list of unready document IDs
  const unreadyDocumentIds = useMemo(() => {
    if (Result.isSuccess(documentsResult)) {
      return documentsResult.value
        .filter((doc) => doc.status !== 'indexed' && doc.status !== 'failed')
        .map((doc) => doc.id)
    }
    return []
  }, [documentsResult])

  useEffect(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    // Only poll if we have unready documents
    if (unreadyDocumentIds.length > 0) {
      // Start polling
      intervalRef.current = setInterval(() => {
        // Poll each unready document individually
        unreadyDocumentIds.forEach((documentId) => {
          refreshDocument({ projectId, documentId }).catch(() => {
            // Silently handle errors - document might have been deleted or become ready
          })
        })
      }, POLL_INTERVAL_MS)
    }

    // Cleanup on unmount or when dependencies change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [unreadyDocumentIds, projectId, refreshDocument])
}
