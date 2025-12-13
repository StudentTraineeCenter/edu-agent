import { chatDetailRoute } from '@/routes/_config'
import { ChatDetailPage } from '@/features/chat/chat-detail-page'

export const ChatDetailRoute = () => {
  const params = chatDetailRoute.useParams()
  return <ChatDetailPage projectId={params.projectId} chatId={params.chatId} />
}
