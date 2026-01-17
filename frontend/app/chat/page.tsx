"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import dynamic from "next/dynamic";
import { chat, type SearchResponse, type ChatResponse } from "@/lib/api";

// Dynamically import the map to avoid SSR issues with Leaflet
const OttawaMap = dynamic(() => import("../components/OttawaMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-[var(--bg-secondary)] rounded-2xl flex items-center justify-center">
      <div className="text-[var(--text-muted)] flex items-center gap-2">
        <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
        Loading map...
      </div>
    </div>
  ),
});

type Message = {
  role: "user" | "assistant";
  content: string;
  data?: SearchResponse;
};

interface SearchResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type?: string;
  class?: string;
  addresstype?: string;
}

  // Thinking messages that cycle while loading
  const THINKING_MESSAGES = [
    "Reading your message",
    "Thinking",
    "Understanding your needs",
    "Searching Ottawa listings",
    "Finding matches",
  ];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingIndex, setLoadingIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<[number, number] | null>(null);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  
  // Smooth cycle through loading messages
  useEffect(() => {
    if (!isLoading) {
      setLoadingIndex(0);
      setIsFading(false);
      return;
    }
    
    const interval = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setLoadingIndex((prev) => (prev + 1) % THINKING_MESSAGES.length);
        setIsFading(false);
      }, 200);
    }, 1800);
    
    return () => clearInterval(interval);
  }, [isLoading]);

  // Close results when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLocationSelect = (lat: number, lng: number) => {
    if (lat === 0 && lng === 0) {
      setSelectedLocation(null);
      setSearchQuery("");
    } else {
      setSelectedLocation([lat, lng]);
    }
  };

  // Search for locations using Nominatim (OpenStreetMap geocoding)
  const searchLocation = async (query: string) => {
    if (query.length < 3) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ", Ottawa, Ontario, Canada")}&limit=3&viewbox=-76.0,45.55,-75.4,45.25&bounded=1`
      );
      const data: SearchResult[] = await response.json();
      setSearchResults(data);
      setShowResults(true);
    } catch (error) {
      console.error("Search error:", error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      searchLocation(value);
    }, 300);
  };

  // Select a search result
  const handleSelectResult = (result: SearchResult) => {
    const lat = parseFloat(result.lat);
    const lng = parseFloat(result.lon);
    setSelectedLocation([lat, lng]);
    setSearchQuery(result.display_name.split(",")[0]);
    setShowResults(false);
  };

  // Generate a simple session ID (persists for the page session)
  const sessionIdRef = useRef<string>(`session_${Date.now()}`);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setIsLoading(true);

    try {
      // Call natural language chat API
      const response = await chat({
        message: text,
        session_id: sessionIdRef.current,
        pinned_lat: selectedLocation?.[0],
        pinned_lng: selectedLocation?.[1],
      });
      
      // Build response message
      let responseText = response.response;
      
      // If there are search results, append them
      if (response.search_results && response.search_results.recommendations?.length > 0) {
        responseText += `\n\nFound ${response.search_results.total_found} apartments! Here are the top matches:\n\n`;
        
        response.search_results.recommendations.slice(0, 5).forEach((rec) => {
          responseText += `${rec.rank}. ${rec.apartment.title}\n`;
          responseText += `   📍 ${rec.apartment.address}, ${rec.apartment.neighborhood}\n`;
          responseText += `   💰 $${rec.apartment.price}/month\n`;
          responseText += `   🚇 ${rec.commute.best_time} min commute\n`;
          responseText += `   ⭐ Score: ${rec.overall_score}/100\n`;
          responseText += `   ${rec.headline}\n\n`;
        });
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: responseText,
          data: response.search_results || undefined,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, something went wrong: ${error instanceof Error ? error.message : 'Unknown error'}. Make sure the backend is running at http://localhost:8000`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex flex-col overflow-hidden">
      {/* Top bar */}
      <header className="flex-shrink-0 border-b border-[var(--border-color)] bg-[var(--bg-primary)]/95 backdrop-blur-lg z-50">
        <div className="flex items-center px-6 h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-70 transition-opacity">
            <Image 
              src="/images/1768631233-trimmy-Nestfinder logo.png" 
              alt="Nestfinder Logo" 
              width={36}
              height={36}
              className="w-9 h-9 object-contain dark:hidden"
            />
            <Image 
              src="/images/nestfinder_logo_trimmed_black.png" 
              alt="Nestfinder Logo" 
              width={36}
              height={36}
              className="w-9 h-9 object-contain hidden dark:block"
            />
            <span className="text-lg font-bold tracking-[-0.02em]">Nestfinder</span>
          </Link>
        </div>
      </header>

      {/* Main content - 50/50 split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left side - Chat */}
        <div className="w-1/2 flex flex-col border-r border-[var(--border-color)]">
          {messages.length === 0 ? (
            /* Empty state */
            <div className="flex-1 flex flex-col items-center justify-center px-6">
              <div className="w-full max-w-lg">
                <div className="text-center mb-6">
                  <h1 className="text-2xl font-semibold tracking-tight animate-slide-up">
                    Chat with Nestfinder
                  </h1>
                  <p className="mt-2 text-sm text-[var(--text-muted)] animate-slide-up-delay-1">
                    Ask me anything about Ottawa apartments — I'm here to help! 🏠
                  </p>
                  {selectedLocation && (
                    <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium animate-slide-up-delay-1">
                      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                      📍 Location pinned for commute calculations
                    </div>
                  )}
                </div>

                {/* Suggested prompts */}
                <div className="grid gap-2 animate-slide-up-delay-2">
                  <Suggestion
                    text="Find me 1-bedroom apartments under $2100 near downtown"
                    onClick={(t) => setInput(t)}
                  />
                  <Suggestion
                    text="I work at 99 Bank St — show me safe areas with good transit"
                    onClick={(t) => setInput(t)}
                  />
                  <Suggestion
                    text="Best neighborhoods for students near uOttawa"
                    onClick={(t) => setInput(t)}
                  />
                </div>
              </div>
            </div>
          ) : (
            /* Messages view */
            <div className="flex-1 overflow-y-auto px-4 py-6">
              <div className="flex flex-col gap-4 max-w-lg mx-auto">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={[
                      "max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed animate-slide-up whitespace-pre-wrap",
                      m.role === "user"
                        ? "ml-auto bg-[var(--accent)] text-white"
                        : "mr-auto bg-[var(--bg-secondary)] text-[var(--text-primary)]",
                    ].join(" ")}
                  >
                    {m.content}
                  </div>
                ))}
                {isLoading && (
                  <div className="mr-auto bg-[var(--bg-secondary)] rounded-2xl px-4 py-3 animate-slide-up">
                    <div className="flex items-center gap-2">
                      <span 
                        className={`text-sm text-[var(--text-muted)] transition-all duration-200 ${isFading ? 'opacity-0' : 'opacity-100'}`}
                      >
                        {THINKING_MESSAGES[loadingIndex]}
                      </span>
                      <span className="flex gap-0.5">
                        <span className="w-1 h-1 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1 h-1 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1 h-1 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Input bar */}
          <div className="flex-shrink-0 p-4 border-t border-[var(--border-color)] bg-[var(--bg-primary)]">
            <div className="flex w-full items-end gap-3 rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-4 py-3 shadow-md dark:shadow-black/30 transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-lg">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Say hi or ask about apartments..."
                rows={1}
                className="max-h-32 w-full resize-none bg-transparent text-sm outline-none placeholder:text-[var(--text-muted)]"
              />

              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="group flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 shadow-md transition-all duration-200 hover:shadow-lg active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:shadow-md"
                aria-label="Send"
              >
                {isLoading ? (
                  <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="transition-transform duration-200 group-hover:-translate-y-0.5"
                  >
                    <path
                      d="M8 3L8 13M8 3L4 7M8 3L12 7"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </button>
            </div>

            <p className="mt-2 text-center text-xs text-[var(--text-muted)]">
              Nestfinder is in beta. Always verify listings manually.
            </p>
          </div>
        </div>

        {/* Right side - Search + Map */}
        <div className="w-1/2 flex flex-col bg-[var(--bg-secondary)]">
          {/* Search bar above map */}
          <div ref={searchRef} className="flex-shrink-0 p-4 pb-0 relative z-10">
            <div className="flex items-center bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)] overflow-hidden shadow-sm transition-all focus-within:border-[var(--accent)] focus-within:shadow-md">
              <div className="pl-4 text-[var(--text-muted)]">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowResults(true)}
                placeholder="Search location in Ottawa..."
                className="w-full px-3 py-3 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none"
              />
              {isSearching && (
                <div className="pr-4">
                  <div className="w-4 h-4 border-2 border-[var(--text-muted)] border-t-transparent rounded-full animate-spin" />
                </div>
              )}
              {searchQuery && !isSearching && (
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSearchResults([]);
                    setSelectedLocation(null);
                  }}
                  className="pr-4 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6 6 18M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>

            {/* Search results dropdown */}
            {showResults && searchResults.length > 0 && (
              <div className="absolute top-full left-4 right-4 mt-2 bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-neutral-700 overflow-hidden z-50">
                <div className="py-1">
                  {searchResults.map((result, index) => {
                    const parts = result.display_name.split(",");
                    const mainName = parts[0].trim();
                    const subAddress = parts.slice(1, 3).map(p => p.trim()).join(", ");

                    return (
                      <button
                        key={result.place_id}
                        onClick={() => handleSelectResult(result)}
                        className={`w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-all duration-150 ${
                          index !== searchResults.length - 1 ? "border-b border-gray-100 dark:border-neutral-800" : ""
                        }`}
                      >
                        {/* Location icon */}
                        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gray-100 dark:bg-neutral-800 flex items-center justify-center">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500 dark:text-gray-400">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                          </svg>
                        </div>
                        
                        {/* Details */}
                        <div className="flex-1 min-w-0">
                          <p className="text-[15px] font-medium text-gray-900 dark:text-white truncate">
                            {mainName}
                          </p>
                          {subAddress && (
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                              {subAddress}
                            </p>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Map */}
          <div className="flex-1 p-4">
            <OttawaMap 
              onLocationSelect={handleLocationSelect}
              selectedLocation={selectedLocation}
            />
          </div>
        </div>
      </div>
    </main>
  );
}

function Suggestion({
  text,
  onClick,
}: {
  text: string;
  onClick: (t: string) => void;
}) {
  return (
    <button
      onClick={() => onClick(text)}
      className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] p-3 text-left text-sm text-[var(--text-secondary)] hover:shadow-glow-card transition-all duration-300"
    >
      {text}
    </button>
  );
}
