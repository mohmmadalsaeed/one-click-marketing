// frontend/src/app/dashboard/inbox/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { format, parseISO } from 'date-fns';

interface Message {
  id: number;
  whatsapp_message_id: string;
  from_phone: string;
  to_phone: string;
  content: string;
  type: string;
  status: string;
  timestamp: string; // ISO string
}

interface InboxResponse {
  messages: Message[];
  total_messages: number;
  current_page: number;
  total_pages: number;
  per_page: number;
}

const ITEMS_PER_PAGE = 15;

export default function InboxPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { toast } = useToast();

  const fetchMessages = useCallback(async (page: number) => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("authToken");
      if (!token) {
        toast({ title: "Authentication Error", description: "Please log in again.", variant: "destructive" });
        setIsLoading(false);
        return;
      }
      const response = await fetch(`/api/v1/messages/inbox?page=${page}&per_page=${ITEMS_PER_PAGE}`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (response.ok) {
        const data: InboxResponse = await response.json();
        // For simplicity, appending new messages. A more robust solution would handle unique messages by ID.
        setMessages(prev => page === 1 ? data.messages : [...prev, ...data.messages].filter((v,i,a)=>a.findIndex(t=>(t.id === v.id))===i));
        setCurrentPage(data.current_page);
        setTotalPages(data.total_pages);
      } else {
        const errorData = await response.json();
        toast({ title: "Error fetching messages", description: errorData.message || "Could not retrieve inbox.", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error", description: "Failed to connect to the server.", variant: "destructive" });
    }
    setIsLoading(false);
  }, [toast]);

  useEffect(() => {
    fetchMessages(1); // Fetch initial page
  }, [fetchMessages]);

  const handleLoadMore = () => {
    if (currentPage < totalPages) {
      fetchMessages(currentPage + 1);
    }
  };
  
  // Group messages by sender for conversation list
  const conversations = messages.reduce((acc, msg) => {
    const key = msg.from_phone; // Assuming incoming messages, so 'from_phone' is the user
    if (!acc[key]) {
      acc[key] = {
        contact: key,
        lastMessage: msg.content,
        lastMessageTimestamp: msg.timestamp,
        unreadCount: 0, // Placeholder for unread count logic
        messages: []
      };
    }
    acc[key].messages.push(msg);
    if (new Date(msg.timestamp) > new Date(acc[key].lastMessageTimestamp)) {
        acc[key].lastMessage = msg.content;
        acc[key].lastMessageTimestamp = msg.timestamp;
    }
    // Implement unread logic if needed
    return acc;
  }, {} as Record<string, { contact: string; lastMessage: string; lastMessageTimestamp: string; unreadCount: number; messages: Message[] }>);

  const sortedConversations = Object.values(conversations).sort((a,b) => 
    new Date(b.lastMessageTimestamp).getTime() - new Date(a.lastMessageTimestamp).getTime()
  );

  const currentConversationMessages = selectedConversation ? conversations[selectedConversation]?.messages.sort((a,b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()) : [];

  return (
    <div className="container mx-auto p-0 md:p-4 h-[calc(100vh-var(--header-height,4rem))] flex flex-col md:flex-row gap-4">
      {/* Conversation List Pane */}
      <Card className="w-full md:w-1/3 lg:w-1/4 flex flex-col h-full">
        <CardHeader>
          <CardTitle>Inbox</CardTitle>
          <CardDescription>Your incoming messages.</CardDescription>
        </CardHeader>
        <ScrollArea className="flex-grow p-2">
          {isLoading && messages.length === 0 && <p className="p-4 text-center">Loading conversations...</p>}
          {!isLoading && sortedConversations.length === 0 && <p className="p-4 text-center">No messages yet.</p>}
          {sortedConversations.map((convo) => (
            <div 
              key={convo.contact}
              className={`p-3 mb-2 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${selectedConversation === convo.contact ? "bg-blue-100 dark:bg-blue-800" : ""}`}
              onClick={() => setSelectedConversation(convo.contact)}
            >
              <div className="flex items-center justify-between">
                <p className="font-semibold">{convo.contact}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {format(parseISO(convo.lastMessageTimestamp), "MMM d, HH:mm")}
                </p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
                {convo.lastMessage}
              </p>
              {/* {convo.unreadCount > 0 && <Badge variant="destructive" className="mt-1">{convo.unreadCount}</Badge>} */}
            </div>
          ))}
          {currentPage < totalPages && !isLoading && (
             <Button onClick={handleLoadMore} variant="outline" className="w-full mt-2">Load More Conversations</Button>
          )}
          {isLoading && messages.length > 0 && <p className="p-4 text-center">Loading more...</p>}
        </ScrollArea>
      </Card>

      {/* Message Display Pane */}
      <Card className="w-full md:w-2/3 lg:w-3/4 flex flex-col h-full">
        <CardHeader>
          <CardTitle>{selectedConversation ? `Chat with ${selectedConversation}` : "Select a conversation"}</CardTitle>
        </CardHeader>
        <ScrollArea className="flex-grow p-4 space-y-4">
          {!selectedConversation && <p className="text-center text-gray-500">Select a conversation to view messages.</p>}
          {currentConversationMessages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.direction === "outgoing" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-xs lg:max-w-md p-3 rounded-lg ${msg.direction === "outgoing" ? "bg-blue-500 text-white" : "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200"}`}>
                <p className="text-sm">{msg.content || msg.incoming_message_content}</p>
                <p className={`text-xs mt-1 ${msg.direction === "outgoing" ? "text-blue-200" : "text-gray-500 dark:text-gray-400"}`}>
                  {format(parseISO(msg.timestamp), "HH:mm")}
                  {msg.direction === "outgoing" && (
                    <Badge variant={msg.status === "read" ? "default" : "secondary"} className="ml-2 text-xs">
                      {msg.status}
                    </Badge>
                  )}
                </p>
              </div>
            </div>
          ))}
        </ScrollArea>
        {/* Reply input - Future enhancement */}
        {selectedConversation && (
          <div className="p-4 border-t dark:border-gray-700">
            <Input placeholder="Type a reply... (Reply functionality not yet implemented)" disabled />
          </div>
        )}
      </Card>
    </div>
  );
}

