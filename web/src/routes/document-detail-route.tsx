import { documentDetailRoute } from './_config'
import { DocumentDetailPage } from '@/features/document/document-detail-page'

export const DocumentDetailRoute = () => {
  const params = documentDetailRoute.useParams()
  return <DocumentDetailPage documentId={params.documentId} />
}
