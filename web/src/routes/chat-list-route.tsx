import { useChatsQuery } from '@/data-acess/chat'
import { projectDetailRoute } from '@/routes/_config'
import { Link } from '@tanstack/react-router'
import type { Chat } from '@/integrations/api'

const ChatItem = ({ chat, projectId }: { chat: Chat; projectId: string }) => (
  <Link
    key={chat.id}
    to="/projects/$projectId/chats/$chatId"
    params={{ projectId, chatId: chat.id }}
  >
    {chat.title}
  </Link>
)

export const ChatListPage = () => {
  const params = projectDetailRoute.useParams()
  const chatsQuery = useChatsQuery(params.projectId)
  const chats = chatsQuery.data

  return (
    <div>
      <h1>Chats</h1>

      <ul>
        {chats?.data.map((chat) => (
          <ChatItem key={chat.id} chat={chat} projectId={params.projectId} />
        ))}
      </ul>
    </div>
  )
}
