"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  function handleSend() {
    const text = input.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");

    // TODO: later connect backend and add assistant response
  }

  return (
    <main className="min-h-screen bg-white text-neutral-900">
      {/* Top bar */}
      <header className="border-b border-neutral-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <Image 
              src="/images/1768631233-trimmy-Nestfinder logo.png" 
              alt="Nestfinder Logo" 
              width={32}
              height={32}
              className="w-8 h-8 object-contain"
            />
            <span className="text-sm font-bold tracking-[-0.02em]">Nestfinder</span>
          </Link>

          <button 
            onClick={() => {
              setMessages([]);
              setInput("");
            }}
            className="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50"
          >
            New chat
          </button>
        </div>
      </header>

      {/* Chat area */}
      <section className="mx-auto flex max-w-4xl flex-col px-6">
        {/* Empty state */}
        {messages.length === 0 && (
          <div className="pt-16 text-center">
            <h1 className="text-3xl font-semibold tracking-tight">
              Ask Nestfinder
            </h1>
            <p className="mt-2 text-sm text-neutral-500">
              Describe what you're looking for and we'll rank Ottawa apartments.
            </p>

            {/* Suggested prompts */}
            <div className="mt-8 grid gap-3 md:grid-cols-2">
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
        )}

        {/* Messages */}
        <div className="mt-10 flex flex-1 flex-col gap-4 pb-40 pt-8">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={[
                "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                m.role === "user"
                  ? "ml-auto bg-[#1F4D2B] text-white"
                  : "mr-auto bg-neutral-100 text-neutral-900",
              ].join(" ")}
            >
              {m.content}
            </div>
          ))}
        </div>
      </section>

      {/* Input bar */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-neutral-200 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl px-6 py-6">
          <div className="flex w-full items-end gap-3 rounded-3xl border border-neutral-300 bg-white px-5 py-4 shadow-lg transition-all focus-within:border-[#1F4D2B] focus-within:shadow-xl">
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
              className="max-h-40 w-full resize-none bg-transparent text-base outline-none placeholder:text-neutral-400"
            />

            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-[#1F4D2B] text-white transition-all hover:bg-opacity-90 disabled:bg-neutral-300 disabled:cursor-not-allowed"
              aria-label="Send message"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="h-5 w-5"
              >
                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
              </svg>
            </button>
          </div>
          
          <p className="mt-3 text-center text-xs text-neutral-400">
            Nestfinder is in beta. Always verify listings manually.
          </p>
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
      className="rounded-2xl border border-neutral-200 bg-white p-4 text-left text-sm text-neutral-700 hover:bg-neutral-50"
    >
      {text}
    </button>
  );
}
