import { ChatRoom } from "@/components/ChatRoom";

export default function ScreeningChatPage({ params }: { params: { chatId: string } }) {
  return <ChatRoom sessionId={params.chatId} />;
}
