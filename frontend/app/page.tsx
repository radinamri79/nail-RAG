/**
 * AI Nail Stylist Chat Page
 * 
 * Full-featured chat interface with FastAPI backend integration
 * 
 * Features:
 * - Real-time messaging with AI assistant
 * - Image upload and analysis (JPEG/PNG/WebP, max 5MB)
 * - Conversation management (pin, delete, rename)
 * - Error handling with user-friendly UI
 * - LocalStorage persistence
 * 
 * API Endpoints (FastAPI @ localhost:8000):
 * - POST /api/chat/conversation - Create conversation
 * - POST /api/chat/message - Send message
 * - POST /api/chat/image - Upload image
 * - DELETE /api/chat/conversation/{id} - Delete conversation
 */

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  ArrowUp,
  Paperclip,
  Plus,
  PanelLeft,
  PanelLeftClose,
  Sparkles,
  Search,
  MoreVertical,
  Pencil,
  Pin,
  Trash2,
  Check,
  X,
  AlertCircle,
} from "lucide-react";

// --- Types ---
type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  image_analysis?: string;
  image?: string; // base64 preview or image URL
};

type ChatSession = {
  id: string;
  conversationId: string;
  title: string;
  preview: string;
  date: string;
  isPinned?: boolean;
  messages: Message[];
};

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:8000';

// --- API Functions ---
async function createConversation(): Promise<{ conversation_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/chat/conversation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    throw new Error(`Failed to create conversation: ${response.statusText}`);
  }
  return response.json();
}

async function sendMessage(conversationId: string, message: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }
  return response.json();
}

async function uploadImage(conversationId: string, file: File, message?: string): Promise<any> {
  const formData = new FormData();
  formData.append('conversation_id', conversationId);
  formData.append('image', file);
  if (message) {
    formData.append('message', message);
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/image`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Failed to upload image: ${response.statusText}`);
  }
  return response.json();
}

async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/conversation/${conversationId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`);
  }
}

function validateImageFile(file: File): { valid: boolean; error?: string } {
  const maxSize = 5 * 1024 * 1024; // 5MB
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  
  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: 'Invalid file type. Please use JPEG, PNG, or WebP.' };
  }
  if (file.size > maxSize) {
    return { valid: false, error: 'File too large. Maximum size is 5MB.' };
  }
  return { valid: true };
}

export default function AIStylistPage() {
  // --- State ---
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Menu State
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  // Chat History State (persisted in localStorage)
  const [history, setHistory] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Image Upload State
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  // --- Load chat history from localStorage ---
  useEffect(() => {
    const savedHistory = localStorage.getItem('nail_chat_history');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setHistory(parsed.map((session: ChatSession) => ({
          ...session,
          messages: session.messages.map((msg: Message) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        })));
      } catch (error) {
        console.error("Failed to parse chat history:", error);
      }
    }
  }, []);

  // --- Save chat history to localStorage ---
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem('nail_chat_history', JSON.stringify(history));
    }
  }, [history]);

  // --- Create conversation on mount ---
  useEffect(() => {
    const initConversation = async () => {
      try {
        const response = await createConversation();
        setConversationId(response.conversation_id);
      } catch (error) {
        console.error("Failed to create conversation:", error);
        setError("Failed to initialize chat. Please refresh the page.");
      }
    };
    initConversation();
  }, []);

  // --- Effects ---
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(
        inputRef.current.scrollHeight,
        120
      )}px`;
    }
  }, [input]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setActiveMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // --- Auto-save current conversation to history ---
  useEffect(() => {
    if (messages.length > 0 && conversationId) {
      const sessionId = currentSessionId || Date.now().toString();
      if (!currentSessionId) {
        setCurrentSessionId(sessionId);
      }

      const firstUserMessage = messages.find((m) => m.role === "user")?.content || "New Chat";
      const title = firstUserMessage.slice(0, 30) + (firstUserMessage.length > 30 ? "..." : "");
      const preview = messages[messages.length - 1]?.content.slice(0, 50) || "";

      setHistory((prev) => {
        const existingIndex = prev.findIndex((s) => s.id === sessionId);
        const newSession: ChatSession = {
          id: sessionId,
          conversationId,
          title,
          preview,
          date: formatDate(new Date()),
          messages: [...messages],
          isPinned: existingIndex >= 0 ? prev[existingIndex].isPinned : false,
        };

        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = newSession;
          return updated;
        }
        return [newSession, ...prev];
      });
    }
  }, [messages, conversationId, currentSessionId]);

  // --- History Actions ---
  const handlePin = useCallback((id: string) => {
    setHistory((prev) => {
      const updated = prev.map((item) =>
        item.id === id ? { ...item, isPinned: !item.isPinned } : item
      );
      localStorage.setItem('nail_chat_history', JSON.stringify(updated));
      return updated;
    });
    setActiveMenuId(null);
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    const session = history.find(s => s.id === id);
    if (session?.conversationId) {
      try {
        await deleteConversation(session.conversationId);
      } catch (error) {
        console.error('Failed to delete conversation from backend:', error);
      }
    }
    
    setHistory((prev) => {
      const updated = prev.filter((item) => item.id !== id);
      localStorage.setItem('nail_chat_history', JSON.stringify(updated));
      return updated;
    });
    setActiveMenuId(null);
    if (currentSessionId === id) {
      handleNewChat();
    }
  }, [history, currentSessionId]);

  const startRename = useCallback((id: string, currentTitle: string) => {
    setRenamingId(id);
    setRenameValue(currentTitle);
    setActiveMenuId(null);
  }, []);

  const saveRename = useCallback(() => {
    if (renamingId && renameValue.trim()) {
      setHistory((prev) => {
        const updated = prev.map((item) =>
          item.id === renamingId ? { ...item, title: renameValue } : item
        );
        localStorage.setItem('nail_chat_history', JSON.stringify(updated));
        return updated;
      });
    }
    setRenamingId(null);
  }, [renamingId, renameValue]);

  const loadSession = useCallback(async (session: ChatSession) => {
    setMessages(session.messages);
    setConversationId(session.conversationId);
    setCurrentSessionId(session.id);
    setError(null);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  }, []);

  // --- Chat Handlers ---
  const handleSend = useCallback(async () => {
    // Check if we have either text or image
    if (!input.trim() && !selectedImage) return;
    if (!conversationId || isLoading) return;
    
    const userText = input.trim() || '📷 [Image uploaded]';
    setInput("");
    setError(null);

    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userText,
      timestamp: new Date(),
      image: selectedImage ? imagePreview || undefined : undefined,
    };
    setMessages((prev) => [...prev, newUserMsg]);
    setIsTyping(true);
    setIsLoading(true);

    try {
      let response;
      
      // If we have an image, upload it with the text/default message
      if (selectedImage) {
        response = await uploadImage(
          conversationId,
          selectedImage,
          input.trim() || "Analyze this nail image"
        );
        setSelectedImage(null);
        setImagePreview(null);
        // Reset file input
        if (fileInputRef.current) fileInputRef.current.value = "";
      } else {
        // Otherwise just send the text message
        response = await sendMessage(conversationId, userText);
      }
      
      const newBotMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        image_analysis: response.image_analysis,
      };
      setMessages((prev) => [...prev, newBotMsg]);
    } catch (error) {
      console.error("Failed to send message:", error);
      setError(
        error instanceof Error
          ? error.message
          : "Failed to send message. Please try again."
      );
      // Remove the user message on error
      setMessages((prev) => prev.filter((m) => m.id !== newUserMsg.id));
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  }, [input, conversationId, isLoading, selectedImage]);

  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validation = validateImageFile(file);
    if (!validation.valid) {
      setError(validation.error || "Invalid file");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    // Just store the image for preview, don't send it yet
    setSelectedImage(file);
    setError(null);

    // Create a preview
    const reader = new FileReader();
    reader.onloadend = () => setImagePreview(reader.result as string);
    reader.readAsDataURL(file);
  }, []);

  const handleNewChat = useCallback(async () => {
    // Don't create new chat if current chat is already empty
    if (messages.length === 0) {
      return;
    }
    
    setMessages([]);
    setCurrentSessionId(null);
    setError(null);
    if (window.innerWidth < 768) setIsSidebarOpen(false);

    try {
      const response = await createConversation();
      setConversationId(response.conversation_id);
    } catch (error) {
      console.error("Failed to create new conversation:", error);
      setError("Failed to create new chat. Please try again.");
    }
  }, [messages.length]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const filteredHistory = history
    .filter((item) =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => (b.isPinned ? 1 : 0) - (a.isPinned ? 1 : 0));

  // --- Helper Functions ---
  function formatDate(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  // --- Render Components ---

  const ErrorBanner = () => {
    if (!error) return null;
    
    return (
      <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-top-2 duration-300">
        <div className="bg-white border-l-4 border-red-500 rounded-xl shadow-xl p-4 max-w-md flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold text-[#3D5A6C] mb-1">Error</h4>
            <p className="text-sm text-gray-600">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  };

  const Sidebar = () => (
    <aside
      className={`
        fixed inset-y-0 left-0 z-50 w-[300px]
        bg-[#F9FAFB]/95 backdrop-blur-xl border-r border-gray-200/60
        transition-transform duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)]
        flex flex-col shadow-2xl md:shadow-lg
        ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"}
      `}
    >
      <div className="flex flex-col h-full w-full">
        <div className="p-4 flex flex-col gap-4 shrink-0 pt-6">
          <div className="flex items-center justify-between">
            <span className="font-bold text-[#3D5A6C] text-lg pl-1 tracking-tight">
              Chats
            </span>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="p-2.5 bg-white shadow-sm border border-gray-100 rounded-xl text-[#3D5A6C] hover:bg-gray-50 transition-all hover:scale-105 active:scale-95"
            >
              <PanelLeftClose className="w-5 h-5" />
            </button>
          </div>

          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-[#D98B99] transition-colors" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-100 border-none rounded-xl py-2 pl-9 pr-3 text-sm text-[#3D5A6C] placeholder-gray-400 focus:ring-2 focus:ring-[#D98B99]/20 focus:bg-white transition-all"
            />
          </div>
        </div>

        <div className="px-4 mb-2 shrink-0">
          <button
            onClick={handleNewChat}
            disabled={isLoading}
            className="w-full flex items-center gap-3 bg-[#F3F4F6] hover:bg-[#E5E7EB] text-[#3D5A6C] font-semibold py-3 px-4 rounded-xl transition-all duration-200 group border border-transparent hover:border-gray-300 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform text-[#D98B99]">
              <Plus className="w-5 h-5" strokeWidth={3} />
            </div>
            <span>New Chat</span>
          </button>
        </div>

        {filteredHistory.length > 0 ? (
          <div className="flex-1 overflow-y-auto px-3 space-y-1 py-2 custom-scrollbar">
            <div className="px-3 pb-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
              Recent
            </div>
            {filteredHistory.map((item) => (
              <div key={item.id} className="relative group">
                {renamingId === item.id ? (
                  <div className="p-2 flex items-center gap-2 bg-white rounded-lg border border-[#D98B99]">
                    <input
                      autoFocus
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      className="flex-1 text-sm text-[#3D5A6C] outline-none bg-transparent"
                      onKeyDown={(e) => e.key === "Enter" && saveRename()}
                    />
                    <button
                      onClick={saveRename}
                      className="text-green-500 hover:text-green-600"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setRenamingId(null)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => loadSession(item)}
                      className={`w-full text-left p-3 rounded-lg hover:bg-white hover:shadow-sm transition-all flex items-center justify-between border ${
                        currentSessionId === item.id
                          ? "bg-white border-[#D98B99]/30 shadow-sm"
                          : "border-transparent"
                      }`}
                    >
                      <div className="flex-1 min-w-0 pr-6">
                        <div className="flex items-center gap-2">
                          {item.isPinned && (
                            <Pin className="w-3 h-3 text-[#D98B99] fill-current" />
                          )}
                          <span className="text-sm font-medium text-[#3D5A6C] truncate block">
                            {item.title}
                          </span>
                        </div>
                        <span className="text-xs text-gray-400 truncate block mt-0.5">
                          {item.date}
                        </span>
                      </div>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveMenuId(
                          activeMenuId === item.id ? null : item.id
                        );
                      }}
                      className={`
                        absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-gray-400 
                        hover:text-[#3D5A6C] hover:bg-gray-200 transition-all 
                        opacity-100 md:opacity-0 md:group-hover:opacity-100 
                        ${
                          activeMenuId === item.id
                            ? "opacity-100 bg-gray-200 text-[#3D5A6C]"
                            : ""
                        }
                      `}
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>

                    {activeMenuId === item.id && (
                      <div
                        ref={menuRef}
                        className="absolute right-0 top-full mt-2 w-48 origin-top-right rounded-xl bg-white shadow-xl border border-gray-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200"
                      >
                        <div className="py-2 px-2">
                          <button
                            onClick={() => startRename(item.id, item.title)}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg flex items-center gap-2 transition-colors"
                          >
                            <Pencil className="w-3.5 h-3.5" /> Rename
                          </button>
                          <button
                            onClick={() => handlePin(item.id)}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg flex items-center gap-2 transition-colors"
                          >
                            <Pin className="w-3.5 h-3.5" />{" "}
                            {item.isPinned ? "Unpin" : "Pin"}
                          </button>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" /> Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-6">
            <p className="text-sm text-gray-400 text-center">
              No chat history yet.<br />Start a conversation!
            </p>
          </div>
        )}
      </div>
    </aside>
  );

  const HeroSection = () => (
    <div className="flex flex-col items-center justify-center h-full px-4 text-center animate-in fade-in duration-700">
      <div className="w-20 h-20 bg-white rounded-3xl shadow-[0_8px_30px_rgba(217,139,153,0.15)] flex items-center justify-center mb-8 rotate-3 transition-transform hover:rotate-6">
        <Sparkles className="w-10 h-10 text-[#D98B99]" />
      </div>

      <h1 className="text-4xl sm:text-5xl font-bold text-[#3D5A6C] leading-[1.1] tracking-tight mb-4">
        Design your nails
      </h1>
      <p className="text-gray-600 text-lg md:text-xl font-light mb-10 max-w-md leading-relaxed">
        Describe a nail design, upload a hand photo, or blend styles to find your
        perfect match.
      </p>

      <div className="flex flex-wrap justify-center gap-3 max-w-2xl w-full">
        {[
          "Create a wedding look 💍",
          "Analyze my hand shape ✋",
          "Match my blue dress 👗",
        ].map((text, i) => (
          <button
            key={i}
            onClick={() => setInput(text)}
            disabled={isLoading}
            className="px-5 py-2.5 bg-white/60 backdrop-blur-sm border border-white/50 text-[#3D5A6C] text-sm font-medium rounded-full hover:bg-white hover:border-[#D98B99]/50 hover:shadow-md transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div
      className={`flex h-screen relative font-sans bg-transparent ${
        messages.length === 0 ? "overflow-hidden" : ""
      }`}
    >
      <ErrorBanner />
      
      {/* Mobile Overlay */}
      <div
        className={`fixed inset-0 bg-[#3D5A6C]/20 backdrop-blur-[2px] z-40 md:hidden transition-opacity duration-300 ${
          isSidebarOpen
            ? "opacity-100 pointer-events-auto"
            : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setIsSidebarOpen(false)}
      />

      <Sidebar />

      <main
        className={`flex-1 flex flex-col relative w-full transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] ${
          isSidebarOpen ? "md:ml-[300px]" : ""
        }`}
      >
        {!isSidebarOpen && (
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="fixed top-4 left-4 z-60 p-2.5 bg-white shadow-sm border border-gray-100 rounded-xl text-[#3D5A6C] hover:bg-white transition-all hover:scale-105 active:scale-95 animate-in fade-in duration-300"
            title="Open Chats"
          >
            <PanelLeft className="w-5 h-5" />
          </button>
        )}

        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center pb-32 md:pb-0">
            <HeroSection />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto px-4 pb-40 pt-16 scrollbar-thin scrollbar-thumb-gray-200/50">
            <div className="max-w-3xl mx-auto space-y-8">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-4 animate-in slide-in-from-bottom-2 duration-500 fade-in`}
                >
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-1 shadow-sm border border-gray-100
                    ${
                      msg.role === "assistant"
                        ? "bg-white text-[#D98B99]"
                        : "bg-white text-gray-600"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <Sparkles className="w-5 h-5" />
                    ) : (
                      <span className="text-xs font-bold">ME</span>
                    )}
                  </div>

                  <div className="flex-1 space-y-2">
                    <p className="font-semibold text-sm text-[#3D5A6C]">
                      {msg.role === "assistant" ? "AI Nail Stylist" : "You"}
                    </p>
                    
                    {/* Image Display - above text as block */}
                    {msg.image && (
                      <div className="block mb-2">
                        <img
                          src={msg.image}
                          alt="Message attachment"
                          className="max-w-[200px] max-h-[250px] w-auto h-auto rounded-lg shadow-sm border border-gray-200 object-contain"
                        />
                      </div>
                    )}
                    
                    <div
                      className={`text-[15px] leading-relaxed text-gray-700 block ${
                        msg.role === "user"
                          ? "bg-white/60 p-3 rounded-2xl rounded-tl-none inline-block shadow-sm"
                          : ""
                      }`}
                    >
                      {msg.content}
                    </div>
                    {msg.image_analysis && (
                      <div className="bg-[#F9FAFB] border border-gray-200 rounded-xl p-3 mt-2">
                        <p className="text-xs font-semibold text-[#D98B99] mb-1">
                          IMAGE ANALYSIS
                        </p>
                        <p className="text-sm text-gray-600">{msg.image_analysis}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex gap-4 animate-in fade-in">
                  <div className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shrink-0 shadow-sm">
                    <Sparkles className="w-5 h-5 text-[#D98B99]" />
                  </div>
                  <div className="flex items-center gap-1.5 h-9 pl-1">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>
          </div>
        )}



        {/* Input Area */}
        <div
          className={`
          fixed right-0 transition-all duration-300 ease-in-out z-20
          ${isSidebarOpen ? "md:left-[300px]" : "left-0"}
          ${
            messages.length > 0
              ? "bottom-0 bg-gradient-to-t from-[#FDF8F9] via-[#FDF8F9]/95 to-transparent pt-10 pb-8"
              : "bottom-0 pb-8 bg-transparent pointer-events-none"
          } 
        `}
        >
          <div className="max-w-2xl mx-auto px-4 md:px-6 w-full relative pointer-events-auto">
            <div className="relative flex flex-col bg-white p-2 rounded-[26px] shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 focus-within:border-[#D98B99]/50 focus-within:shadow-[0_8px_30px_rgba(217,139,153,0.1)] transition-all duration-300 group">
              {/* Image Preview inside chat box */}
              {imagePreview && (
                <div className="flex items-center gap-2 px-2 pt-2 pb-2">
                  <div className="relative w-12 h-12 rounded-lg overflow-visible bg-gray-100 shrink-0">
                    <img src={imagePreview} alt="preview" className="w-12 h-12 rounded-lg object-cover" />
                    <button
                      onClick={() => { 
                        setImagePreview(null); 
                        setSelectedImage(null);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      className="absolute -top-2 -right-2 w-5 h-5 bg-gray-700 hover:bg-gray-800 rounded-full flex items-center justify-center transition-colors shadow-sm"
                    >
                      <X className="w-3 h-3 text-white" />
                    </button>
                  </div>
                  <span className="text-xs text-gray-500 truncate max-w-[150px]">{selectedImage?.name}</span>
                </div>
              )}
              
              <div className="flex items-end gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleImageUpload}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!conversationId || isLoading}
                className="p-2.5 mb-2 text-gray-400 hover:text-[#3D5A6C] hover:bg-gray-50 rounded-full transition-colors shrink-0 ml-1 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Upload Photo"
              >
                <Paperclip className="w-5 h-5" />
              </button>

              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={!conversationId || isLoading}
                placeholder={
                  !conversationId
                    ? "Initializing chat..."
                    : isLoading
                    ? "Sending..."
                    : "Ask anything..."
                }
                className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-[#3D5A6C] placeholder:text-gray-300 py-3.5 resize-none max-h-[120px] min-h-[52px] text-[16px] leading-relaxed disabled:opacity-50"
                rows={1}
              />

              <button
                onClick={handleSend}
                disabled={(!input.trim() && !selectedImage) || !conversationId || isLoading}
                className={`
                  w-10 h-10 aspect-square rounded-full flex items-center justify-center mb-2 mr-1 transition-all duration-200 shadow-sm shrink-0
                  ${
                    (input.trim() || selectedImage) && conversationId && !isLoading
                      ? "bg-[#3D5A6C] text-white hover:bg-[#2F4A58] scale-100"
                      : "bg-gray-100 text-gray-300 scale-95 cursor-not-allowed"
                  }
                `}
              >
                <ArrowUp className="w-5 h-5 stroke-[3px]" />
              </button>
              </div>
            </div>

            <div className="text-center mt-2">
              <p className="text-[10px] text-gray-400 font-medium opacity-60">
                AI can make mistakes. Check important info.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
