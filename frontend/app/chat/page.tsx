"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import ThemeTogglePill from "../components/ThemeTogglePill";
import { searchApartments, type SearchResponse } from "@/lib/api";
import { parseUserMessage } from "@/lib/parseUserInput";

type Message = {
  role: "user" | "assistant";
  content: string;
  data?: SearchResponse;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setIsLoading(true);

    try {
      // Parse user input
      const parsed = parseUserMessage(text);
      
      if (!parsed) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "I couldn't find a work address in your message. Please include where you work (e.g., '99 Bank St' or 'downtown Ottawa') so I can calculate commute times.",
          },
        ]);
        setIsLoading(false);
        return;
      }

      // Call backend API
      const response = await searchApartments(parsed);
      
      // Format response message
      let responseText = `Found ${response.total_found} apartments! Here are the top matches:\n\n`;
      
      response.recommendations.slice(0, 5).forEach((rec) => {
        responseText += `${rec.rank}. ${rec.apartment.title}\n`;
        responseText += `   📍 ${rec.apartment.address}, ${rec.apartment.neighborhood}\n`;
        responseText += `   💰 $${rec.apartment.price}/month\n`;
        responseText += `   🚇 ${rec.commute.best_time} min commute\n`;
        responseText += `   ⭐ Score: ${rec.overall_score}/100\n`;
        responseText += `   ${rec.headline}\n\n`;
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: responseText,
          data: response,
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
    <main className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-50 border-b border-[var(--border-color)] bg-[var(--bg-primary)]/95 backdrop-blur-lg">
        <div className="mx-auto flex max-w-4xl items-center px-6 h-20">
          <Link href="/" className="flex items-center gap-3 hover:opacity-70 transition-opacity">
            <Image 
              src="/images/1768631233-trimmy-Nestfinder logo.png" 
              alt="Nestfinder Logo" 
              width={44}
              height={44}
              className="w-11 h-11 object-contain dark:hidden"
            />
            <Image 
              src="/images/nestfinder_logo_trimmed_black.png" 
              alt="Nestfinder Logo" 
              width={44}
              height={44}
              className="w-11 h-11 object-contain hidden dark:block"
            />
            <span className="text-xl font-bold tracking-[-0.02em]">Nestfinder</span>
          </Link>
        </div>
      </header>

      {/* Chat area */}
      {messages.length === 0 ? (
        /* Empty state - centered */
        <section className="flex-1 flex items-center justify-center px-6">
          <div className="w-full max-w-4xl">
            <div className="text-center mb-8">
            <h1 className="text-3xl font-semibold tracking-tight animate-slide-up">
              Ask Nestfinder
            </h1>
            <p className="mt-2 text-sm text-[var(--text-muted)] animate-slide-up-delay-1">
              Describe what you're looking for and we'll rank Ottawa apartments.
            </p>

              {/* Suggested prompts */}
              <div className="mt-8 grid gap-3 md:grid-cols-2 animate-slide-up-delay-2">
                <Suggestion
                  text="Find me 1-bedroom apartments under $2100 near downtown with a short commute"
                  onClick={(t) => setInput(t)}
                />
                <Suggestion
                  text="I work at 99 Bank St — show me safe, quiet areas with good transit"
                  onClick={(t) => setInput(t)}
                />
                <Suggestion
                  text="Best neighborhoods for students near uOttawa with in-unit laundry"
                  onClick={(t) => setInput(t)}
                />
                <Suggestion
                  text="Compare Centretown vs Sandy Hill for walkability + nightlife"
                  onClick={(t) => setInput(t)}
                />
              </div>
            </div>

            {/* Input bar - centered */}
            <div className="w-full">
              <div className="flex w-full items-end gap-4 rounded-2xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-5 py-4 shadow-lg dark:shadow-black/40 transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-xl animate-slide-up">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask about Ottawa apartments..."
                  rows={1}
                  className="max-h-40 w-full resize-none bg-transparent text-base outline-none placeholder:text-[var(--text-muted)]"
                />

                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="group flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 shadow-md transition-all duration-200 hover:shadow-lg active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:shadow-md"
                  aria-label="Send"
                >
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg
                      width="18"
                      height="18"
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

              <p className="mt-3 text-center text-xs text-[var(--text-muted)]">
                Nestfinder is in beta. Always verify listings manually.
              </p>
            </div>

            {/* Footer - centered with content */}
            <div className="mt-8 pt-6 border-t border-[var(--border-color)]">
              <div className="flex flex-col items-center gap-4">
                <ThemeTogglePill />
                <p className="text-xs text-[var(--text-muted)]">
                  © 2026 Nestfinder. All rights reserved.
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : (
        /* Messages view - normal layout */
        <>
          <section className="mx-auto flex max-w-4xl flex-col px-6 flex-1">
            {/* Messages */}
            <div className="mt-10 flex flex-1 flex-col gap-4 pb-32 pt-8">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={[
                    "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed animate-slide-up",
                    m.role === "user"
                      ? "ml-auto bg-[var(--accent)] text-white"
                      : "mr-auto bg-[var(--bg-secondary)] text-[var(--text-primary)]",
                  ].join(" ")}
                >
                  {m.content}
                </div>
              ))}
            </div>
          </section>

          {/* Input bar - fixed at bottom */}
          <div className="fixed bottom-0 left-0 right-0 bg-[var(--bg-primary)]/95 backdrop-blur-lg border-t border-[var(--border-color)]">
            <div className="mx-auto max-w-4xl px-6 py-4">
              <div className="flex w-full items-end gap-4 rounded-2xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-5 py-4 shadow-lg dark:shadow-black/40 transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-xl">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask about Ottawa apartments..."
                  rows={1}
                  className="max-h-40 w-full resize-none bg-transparent text-base outline-none placeholder:text-[var(--text-muted)]"
                />

                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="group flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 shadow-md transition-all duration-200 hover:shadow-lg active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:shadow-md"
                  aria-label="Send"
                >
                  <svg
                    width="18"
                    height="18"
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
                </button>
              </div>

              <div className="mt-2 flex items-center justify-between">
                <p className="text-xs text-[var(--text-muted)]">
                  Nestfinder is in beta. Always verify listings manually.
                </p>
                <ThemeTogglePill />
              </div>
            </div>
          </div>
        </>
      )}
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
      className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] p-4 text-left text-sm text-[var(--text-secondary)] hover:shadow-glow-card transition-all duration-300"
    >
      {text}
    </button>
  );
}
