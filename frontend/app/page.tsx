'use client';

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect, useRef, ReactNode } from "react";
import ThemeTogglePill from "./components/ThemeTogglePill";
import LogoMarquee from "./components/LogoMarquee";
import { MapPin, Clock, Shield, DollarSign, Sparkles, Zap, Brain, Github } from "lucide-react";

// Scroll-triggered animation component
function AnimateOnScroll({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), delay);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.2, rootMargin: "0px 0px -50px 0px" }
    );
    
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [delay]);
  
  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'} ${className}`}
    >
      {children}
    </div>
  );
}

// Timeline with buttery smooth moving dot
function TimelineWithMovingDot() {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineAreaRef = useRef<HTMLDivElement>(null);
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [activeStep, setActiveStep] = useState(-1);
  const [dotY, setDotY] = useState(0);
  const [lineHeight, setLineHeight] = useState(0);
  const animationRef = useRef<number>();
  const targetY = useRef(0);
  const currentY = useRef(0);
  
  useEffect(() => {
    // Buttery smooth animation loop
    const animate = () => {
      const ease = 0.15; // Responsive but smooth
      const diff = targetY.current - currentY.current;
      
      if (Math.abs(diff) > 0.5) {
        currentY.current += diff * ease;
      } else {
        currentY.current = targetY.current;
      }
      
      setDotY(currentY.current);
      setLineHeight(Math.max(0, currentY.current + 8));
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);
  
  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current || !timelineAreaRef.current || stepRefs.current.length === 0) return;
      
      const timelineRect = timelineAreaRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      
      // Get positions of first and last steps
      const firstStep = stepRefs.current[0];
      const lastStep = stepRefs.current[stepRefs.current.length - 1];
      if (!firstStep || !lastStep) return;
      
      const firstRect = firstStep.getBoundingClientRect();
      const lastRect = lastStep.getBoundingClientRect();
      
      // Calculate Y positions relative to timeline container
      const firstY = firstRect.top - timelineRect.top + firstRect.height / 2;
      const lastY = lastRect.top - timelineRect.top + lastRect.height / 2;
      
      // Trigger point - 45% from top of viewport
      const triggerPoint = viewportHeight * 0.45;
      
      // Calculate scroll progress through the timeline
      // Start: when first step hits trigger point
      // End: when last step hits trigger point
      const scrollStart = firstRect.top - triggerPoint;
      const scrollEnd = lastRect.top - triggerPoint;
      const scrollRange = scrollEnd - scrollStart;
      
      let progress = 0;
      if (scrollRange !== 0) {
        progress = -scrollStart / scrollRange;
      }
      
      // Clamp progress between 0 and 1
      progress = Math.max(0, Math.min(1, progress));
      
      // Interpolate dot position between first and last step
      const targetPos = firstY + (lastY - firstY) * progress;
      targetY.current = targetPos;
      
      // Determine active step based on progress
      const stepCount = stepRefs.current.length;
      const activeIdx = Math.min(stepCount - 1, Math.floor(progress * stepCount + 0.3));
      setActiveStep(progress > 0.05 ? activeIdx : -1);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleScroll, { passive: true });
    
    // Initial call
    requestAnimationFrame(handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, []);

  const steps = [
    {
      time: "0:00",
      title: "Tell us what matters",
      desc: "Type naturally. \"Pet-friendly 1BR under $1700 with short commute to Shopify.\" We get it.",
      align: "right"
    },
    {
      time: "0:03",
      title: "We scan everything",
      desc: "160+ listings from Kijiji, Zumper, Homestead. Commute times calculated. Safety scores checked.",
      align: "left"
    },
    {
      time: "0:05",
      title: "Your shortlist appears",
      desc: "Top matches ranked by what you care about. Click through to apply directly.",
      align: "right"
    }
  ];

  return (
    <div ref={containerRef} className="relative max-w-3xl mx-auto">
      <AnimateOnScroll>
        <div className="text-center mb-16">
          <h3 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">
            Your apartment search,<br />reimagined
          </h3>
        </div>
      </AnimateOnScroll>
      
      {/* Timeline container */}
      <div ref={timelineAreaRef} className="relative">
        {/* Timeline line - static background */}
        <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-[2px] bg-[var(--border-color)] md:-translate-x-1/2 rounded-full" />
        
        {/* Timeline line - filled progress with glow */}
        <div 
          className="absolute left-8 md:left-1/2 top-0 w-[2px] bg-[var(--accent)] md:-translate-x-1/2 rounded-full"
          style={{ 
            height: lineHeight,
            boxShadow: '0 0 12px rgba(31, 77, 43, 0.5)'
          }}
        />
        
        {/* Single moving dot - buttery smooth */}
        <div 
          className="absolute left-8 md:left-1/2 -translate-x-1/2 z-20 pointer-events-none"
          style={{ top: dotY }}
        >
          {/* Outer glow */}
          <div className="absolute -inset-3 rounded-full bg-[var(--accent)]/20 blur-md" />
          {/* Main dot */}
          <div className="relative w-4 h-4 rounded-full bg-[var(--accent)] shadow-lg -translate-y-1/2">
            <div className="absolute inset-0 rounded-full bg-[var(--accent)] animate-ping opacity-40" />
            <div className="absolute inset-[3px] rounded-full bg-white/30" />
          </div>
        </div>
        
        <div className="space-y-20 pt-2">
          {steps.map((step, i) => (
            <div 
              key={i}
              ref={el => { stepRefs.current[i] = el; }}
            >
              <AnimateOnScroll delay={i * 100}>
                <div 
                  className={`relative flex items-start gap-6 ${step.align === 'left' ? 'md:flex-row-reverse md:text-right' : ''}`}
                >
                  {/* Step marker - lights up when active */}
                  <div 
                    className={`absolute left-8 md:left-1/2 w-3 h-3 rounded-full -translate-x-1/2 z-10 transition-all duration-500 ${
                      activeStep >= i 
                        ? 'bg-[var(--accent)] scale-125 shadow-lg shadow-[var(--accent)]/50' 
                        : 'bg-[var(--bg-secondary)] border-2 border-[var(--border-color)]'
                    }`} 
                  />
                  
                  {/* Time badge */}
                  <div className="hidden md:block w-24 flex-shrink-0">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-bold transition-all duration-500 ${
                      activeStep >= i
                        ? 'bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/30'
                        : 'bg-[var(--accent)]/10 text-[var(--accent)]'
                    }`}>
                      {step.time}
                    </span>
                  </div>
                  
                  {/* Content */}
                  <div className={`flex-1 ml-14 md:ml-0 ${step.align === 'left' ? 'md:mr-14' : 'md:ml-14'}`}>
                    <div className={`group p-6 rounded-2xl border transition-all duration-500 ${
                      activeStep >= i
                        ? 'bg-[var(--bg-card)] border-[var(--accent)]/30 shadow-xl shadow-[var(--accent)]/5'
                        : 'bg-[var(--bg-card)] border-[var(--border-color)]'
                    } hover:border-[var(--accent)]/50 hover:shadow-2xl hover:-translate-y-1`}>
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-500 ${
                          activeStep >= i
                            ? 'bg-[var(--accent)] scale-110'
                            : 'bg-[var(--accent)]/10 group-hover:bg-[var(--accent)] group-hover:scale-110'
                        }`}>
                          {i === 0 && <Brain className={`w-4 h-4 transition-colors duration-500 ${activeStep >= i ? 'text-white' : 'text-[var(--accent)] group-hover:text-white'}`} />}
                          {i === 1 && <Zap className={`w-4 h-4 transition-colors duration-500 ${activeStep >= i ? 'text-white' : 'text-[var(--accent)] group-hover:text-white'}`} />}
                          {i === 2 && <MapPin className={`w-4 h-4 transition-colors duration-500 ${activeStep >= i ? 'text-white' : 'text-[var(--accent)] group-hover:text-white'}`} />}
                        </div>
                        <h4 className="text-lg font-semibold text-[var(--text-primary)]">{step.title}</h4>
                      </div>
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                  
                  {/* Spacer for alignment */}
                  <div className="hidden md:block w-24 flex-shrink-0" />
                </div>
              </AnimateOnScroll>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Thinking messages that cycle while loading (same as chat page)
const THINKING_MESSAGES = [
  "Reading your message",
  "Thinking",
  "Understanding your needs",
  "Searching Ottawa listings",
  "Finding matches",
];

// AI Response for the demo
const AI_RESPONSE = `Found 14 apartments matching your criteria! Here are my top picks:

**1. The Laurier** - $1,695/mo
📍 Sandy Hill • 1 bed • 12 min transit
⭐ Score: 92/100 - Best Overall Match
✓ Pet-friendly • In-unit laundry

**2. Holbrook** - $1,349/mo
📍 Centretown • Studio • 8 min transit
⭐ Score: 89/100 - Best Value
✓ Gym • Rooftop terrace

**3. 321 Waverley** - $1,450/mo
📍 The Glebe • 1 bed • 15 min transit
⭐ Score: 87/100 - Safest Area
✓ Parking included • Near parks

**4. Island Park Towers** - $1,249/mo
📍 Westboro • Studio • 18 min transit
⭐ Score: 85/100 - Most Walkable
✓ Steps from shops & cafes

View all 14 results →`;

// Demo apartment markers for the mini map
const DEMO_APARTMENTS = [
  { id: 1, top: '28%', left: '52%', price: '$1,695' },
  { id: 2, top: '42%', left: '48%', price: '$1,349' },
  { id: 3, top: '55%', left: '58%', price: '$1,450' },
  { id: 4, top: '35%', left: '32%', price: '$1,249' },
];

// Streaming text component for demo
function DemoStreamingText({ text, isActive }: { text: string; isActive: boolean }) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  
  useEffect(() => {
    if (!isActive) {
      setDisplayedText("");
      setIsComplete(false);
      return;
    }
    
    let index = 0;
    const speed = 12; // ms per character
    
    const timer = setInterval(() => {
      if (index < text.length) {
        const chunkSize = Math.random() > 0.7 ? 3 : 1;
        const nextIndex = Math.min(index + chunkSize, text.length);
        setDisplayedText(text.slice(0, nextIndex));
        index = nextIndex;
      } else {
        clearInterval(timer);
        setIsComplete(true);
      }
    }, speed);
    
    return () => clearInterval(timer);
  }, [text, isActive]);
  
  // Parse markdown-like formatting
  const formatText = (content: string) => {
    return content.split('\n').map((line, i) => {
      // Bold **text**
      const boldRegex = /\*\*(.*?)\*\*/g;
      const parts = line.split(boldRegex);
      
      return (
        <span key={i}>
          {parts.map((part, j) => {
            if (j % 2 === 1) {
              return <span key={j} className="font-semibold">{part}</span>;
            }
            // Check for link text
            if (part.includes("View all")) {
              return <span key={j} className="text-blue-600 dark:text-blue-400 underline cursor-pointer">{part}</span>;
            }
            return <span key={j}>{part}</span>;
          })}
          {i < content.split('\n').length - 1 && '\n'}
        </span>
      );
    });
  };
  
  return (
    <>
      {formatText(displayedText)}
      {!isComplete && isActive && <span className="inline-block w-1.5 h-4 bg-[var(--text-muted)] ml-0.5 animate-pulse" />}
    </>
  );
}

// Interactive Demo Component - Matches actual chat interface
function LiveDemo() {
  const [phase, setPhase] = useState(0);
  const [typedText, setTypedText] = useState("");
  const [userInput, setUserInput] = useState("");
  const [isAutoTyping, setIsAutoTyping] = useState(false);
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);
  const [isUserInteracting, setIsUserInteracting] = useState(false);
  const [locationSearch, setLocationSearch] = useState("");
  const [pinPosition, setPinPosition] = useState({ top: '35%', left: '45%' });
  const [showPin, setShowPin] = useState(true);
  const query = "Find me 1-bedroom apartments under $2100 near downtown";
  
  // Cycle through thinking messages
  useEffect(() => {
    if (phase !== 1) return;
    
    const interval = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setThinkingIndex((prev) => (prev + 1) % THINKING_MESSAGES.length);
        setIsFading(false);
      }, 200);
    }, 1200);
    
    return () => clearInterval(interval);
  }, [phase]);
  
  useEffect(() => {
    // Don't auto-run if user is interacting
    if (isUserInteracting) return;
    
    const runDemo = async () => {
      // Reset
      setPhase(0);
      setTypedText("");
      setThinkingIndex(0);
      await new Promise(r => setTimeout(r, 1000));
      
      // Phase 0: Start typing
      setIsAutoTyping(true);
      for (let i = 0; i <= query.length; i++) {
        setTypedText(query.slice(0, i));
        await new Promise(r => setTimeout(r, 40));
      }
      setIsAutoTyping(false);
      await new Promise(r => setTimeout(r, 500));
      
      // Phase 1: Processing
      setPhase(1);
      await new Promise(r => setTimeout(r, 3000));
      
      // Phase 2: Show results (streaming animation takes ~4s, then pause to read)
      setPhase(2);
      await new Promise(r => setTimeout(r, 8000));
    };
    
    runDemo();
    const interval = setInterval(runDemo, 16000);
    return () => clearInterval(interval);
  }, [isUserInteracting]);

  // Handle user sending a message
  const handleSend = () => {
    if (!userInput.trim()) return;
    setIsUserInteracting(true);
    setTypedText(userInput);
    setUserInput("");
    setPhase(1);
    setThinkingIndex(0);
    
    // Show response after delay
    setTimeout(() => {
      setPhase(2);
    }, 2500);
  };

  return (
    <div className="relative">
      {/* Browser Chrome */}
      <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-2xl">
        {/* Title Bar */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
            <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
            <div className="w-3 h-3 rounded-full bg-[#28c840]" />
          </div>
          <div className="flex-1 mx-4">
            <div className="max-w-md mx-auto px-4 py-1.5 rounded-lg bg-[var(--bg-primary)] text-xs text-[var(--text-muted)] text-center">
              nestfinder.app/chat
            </div>
          </div>
        </div>
        
        {/* Chat Interface - Matches actual chat page */}
        <div className="flex min-h-[420px] bg-[var(--bg-primary)]">
          {/* Left: Chat */}
          <div className="w-1/2 flex flex-col border-r border-[var(--border-color)]">
            {/* Messages */}
            <div className="flex-1 overflow-hidden px-4 py-6">
              <div className="flex flex-col gap-4 max-w-sm mx-auto">
                {/* Empty state header (when no messages) */}
                {phase === 0 && !typedText && (
                  <div className="text-center py-8 animate-fade-in">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                      Chat with Nestfinder
                    </h3>
                    <p className="text-sm text-[var(--text-muted)]">
                      Ask me anything about Ottawa apartments
                    </p>
                  </div>
                )}
                
                {/* User message */}
                {typedText && (
                  <div className="ml-auto max-w-[85%] rounded-2xl px-4 py-3 text-sm bg-[var(--accent)] text-white animate-slide-up">
                    {typedText}
                    {isAutoTyping && <span className="inline-block w-0.5 h-4 bg-white ml-0.5 animate-pulse" />}
                  </div>
                )}
                
                {/* Thinking state */}
                {phase === 1 && (
                  <div className="mr-auto bg-[var(--bg-secondary)] rounded-2xl px-4 py-3 animate-slide-up">
                    <div className="flex items-center gap-2">
                      <span 
                        className={`text-sm text-[var(--text-muted)] transition-all duration-200 ${isFading ? 'opacity-0' : 'opacity-100'}`}
                      >
                        {THINKING_MESSAGES[thinkingIndex]}
                      </span>
                      <span className="flex gap-0.5">
                        <span className="w-1 h-1 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1 h-1 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1 h-1 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </span>
                    </div>
                  </div>
                )}
                
                {/* AI Response - Streaming */}
                {phase === 2 && (
                  <div className="mr-auto max-w-[90%] rounded-2xl px-4 py-3 text-sm bg-[var(--bg-secondary)] text-[var(--text-primary)] animate-slide-up whitespace-pre-wrap">
                    <DemoStreamingText text={AI_RESPONSE} isActive={phase === 2} />
                  </div>
                )}
              </div>
            </div>
            
            {/* Input bar - INTERACTIVE */}
            <div className="flex-shrink-0 p-4 border-t border-[var(--border-color)]">
              <div className="flex items-center gap-3 rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-4 py-3 shadow-sm focus-within:border-[var(--accent)] focus-within:shadow-md transition-all">
                <input
                  type="text"
                  value={userInput}
                  onChange={(e) => {
                    setUserInput(e.target.value);
                    if (!isUserInteracting && e.target.value) {
                      setIsUserInteracting(true);
                      setTypedText("");
                      setPhase(0);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Say hi or ask about apartments..."
                  className="flex-1 text-sm bg-transparent outline-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                />
                <button
                  onClick={handleSend}
                  disabled={!userInput.trim()}
                  className="w-8 h-8 rounded-full bg-neutral-900 dark:bg-white flex items-center justify-center disabled:opacity-30 hover:opacity-80 transition-opacity"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="text-white dark:text-neutral-900">
                    <path d="M8 3L8 13M8 3L4 7M8 3L12 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          {/* Right: Map - Interactive */}
          <div className="w-1/2 bg-[var(--bg-secondary)] p-4 flex flex-col">
            {/* Search bar - Interactive */}
            <div className="mb-3">
              <div className="flex items-center bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)] px-4 py-2.5 focus-within:border-[var(--accent)] transition-colors">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--text-muted)] mr-2 flex-shrink-0">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
                <input
                  type="text"
                  value={locationSearch}
                  onChange={(e) => setLocationSearch(e.target.value)}
                  placeholder="Search location in Ottawa..."
                  className="flex-1 text-sm bg-transparent outline-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                />
                {locationSearch && (
                  <button
                    onClick={() => setLocationSearch("")}
                    className="text-[var(--text-muted)] hover:text-[var(--text-primary)] ml-2"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6 6 18M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
            
            {/* Real Map - OpenStreetMap - Clickable */}
            <div 
              className="flex-1 rounded-2xl border border-[var(--border-color)] relative overflow-hidden cursor-crosshair"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                setPinPosition({ top: `${y}%`, left: `${x}%` });
                setShowPin(true);
              }}
            >
              <iframe
                src="https://www.openstreetmap.org/export/embed.html?bbox=-75.7871%2C45.3503%2C-75.6171%2C45.4503&layer=mapnik"
                className="w-full h-full border-0 pointer-events-none"
                style={{ filter: 'saturate(0.9) contrast(1.05)' }}
                loading="lazy"
                title="Ottawa Map"
              />
              
              {/* Overlay - 📍 emoji pin - Repositionable */}
              {showPin && (
                <div className="absolute inset-0 pointer-events-none">
                  <div 
                    className="absolute -translate-x-1/2 -translate-y-full transition-all duration-200"
                    style={{ top: pinPosition.top, left: pinPosition.left }}
                  >
                    <span className="text-4xl drop-shadow-lg" style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' }}>📍</span>
                  </div>
                </div>
              )}
              
              {/* Apartment markers - show when results are displayed */}
              {phase === 2 && (
                <div className="absolute inset-0 pointer-events-none">
                  {DEMO_APARTMENTS.map((apt, i) => (
                    <div
                      key={apt.id}
                      className="absolute -translate-x-1/2 -translate-y-1/2 animate-scale-in"
                      style={{ 
                        top: apt.top, 
                        left: apt.left,
                        animationDelay: `${i * 150}ms`
                      }}
                    >
                      {/* Marker circle */}
                      <div className="relative group cursor-pointer pointer-events-auto">
                        <div className="w-7 h-7 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-xs font-bold shadow-lg border-2 border-white">
                          {apt.id}
                        </div>
                        {/* Price tooltip */}
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-black/80 text-white text-[10px] font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                          {apt.price}/mo
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Legend & Clear button */}
              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
                <div className="px-3 py-2 rounded-lg bg-white/95 dark:bg-black/80 backdrop-blur shadow-lg border border-gray-200/60 dark:border-gray-700/60 text-xs pointer-events-auto">
                  <p className="text-gray-500 dark:text-gray-400 font-medium">
                    {phase === 2 ? "🏠 4 matches shown" : showPin ? "📍 Location set" : "Click to drop a pin"}
                  </p>
                </div>
                {showPin && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowPin(false);
                    }}
                    className="px-3 py-2 rounded-lg bg-white/95 dark:bg-black/80 backdrop-blur shadow-lg border border-gray-200/60 dark:border-gray-700/60 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors pointer-events-auto"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  );
}

export default function Home() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const stats = [
    { value: "5,000+", label: "Apartments Analyzed" },
    { value: "95%", label: "User Satisfaction" },
    { value: "30min", label: "Average Time Saved" },
    { value: "24/7", label: "AI Assistant" }
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Navbar */}
      <header className={`sticky top-0 z-50 w-full border-b border-[var(--border-color)] transition-all duration-300 ${
        isScrolled 
          ? 'bg-[var(--bg-primary)]/95 backdrop-blur-lg shadow-md' 
          : 'bg-[var(--bg-primary)]/80 backdrop-blur-md'
      }`}>
        <nav className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Left: Logo + Text */}
            <div className="flex items-center gap-3">
              <Image 
                src="/images/1768631233-trimmy-Nestfinder logo.png" 
                alt="Nestfinder Logo" 
                width={44}
                height={44}
                className="w-11 h-11 object-contain dark:hidden"
                priority
              />
              <Image 
                src="/images/nestfinder_logo_trimmed_black.png" 
                alt="Nestfinder Logo" 
                width={44}
                height={44}
                className="w-11 h-11 object-contain hidden dark:block"
                priority
              />
              <span className="text-xl font-bold tracking-[-0.02em] text-[var(--text-primary)]">Nestfinder</span>
            </div>

            {/* Right: CTA Buttons */}
            <div className="flex items-center gap-3">
              <button className="hidden sm:inline-flex items-center px-4 py-2 text-sm rounded-lg border border-[var(--border-color)] text-[var(--text-primary)] font-medium hover:shadow-glow-subtle hover:border-[var(--accent)] transition-all duration-300">
                Try Demo
              </button>
              <Link
                href="/chat"
                className="inline-flex items-center px-4 py-2 text-sm rounded-lg bg-[var(--accent)] text-white font-medium hover:shadow-glow transition-all duration-300"
              >
                Get Started
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section with Gradient Background */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent-light)] via-transparent to-transparent opacity-30" />
        
        <div className="relative max-w-6xl mx-auto px-6 lg:px-8 pt-20 pb-16 md:pt-32 md:pb-24">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold text-[var(--text-primary)] tracking-tight mb-6 animate-slide-up">
              Find the best apartments<br/>in{" "}
              <span className="text-gradient underline-zigzag">Ottawa</span>{" "}
              — fast.
            </h1>
            <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-3xl mx-auto mb-10 animate-slide-up-delay-1">
              NestFinder ranks rentals by commute, safety, walkability, and price based on your priorities. No more endless scrolling through listings.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-slide-up-delay-2">
              <Link
                href="/chat"
                className="group w-full sm:w-auto inline-flex items-center justify-center px-6 py-2.5 text-sm rounded-lg bg-[var(--accent)] text-white font-medium hover:shadow-glow transition-all duration-300"
              >
                Start Your Search
              </Link>
              <button className="group w-full sm:w-auto inline-flex items-center justify-center px-6 py-2.5 text-sm rounded-lg border border-[var(--border-color)] text-[var(--text-primary)] font-medium hover:shadow-glow-subtle hover:border-[var(--accent)] transition-all duration-300">
                Watch Demo
              </button>
            </div>

            {/* Hero Visual - Enhanced */}
            <div className="max-w-5xl mx-auto animate-fade-in-slow">
              <div className="relative bg-gradient-to-br from-[var(--bg-secondary)] to-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-3xl p-8 shadow-2xl">
                <div className="aspect-video bg-[var(--bg-primary)] rounded-2xl border border-[var(--border-color)] flex items-center justify-center overflow-hidden">
                  <p className="text-[var(--text-muted)] font-medium text-lg">Video placeholder</p>
                </div>
                {/* Floating Elements */}
                <div className="absolute -top-4 -right-4 w-24 h-24 bg-[var(--accent)] rounded-2xl opacity-20 blur-2xl" />
                <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-[var(--accent)] rounded-2xl opacity-10 blur-3xl" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-12 md:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="text-center animate-fade-in-slow" style={{ animationDelay: `${index * 0.1}s` }}>
              <div className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-2">{stat.value}</div>
              <div className="text-sm text-[var(--text-secondary)]">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Logo Marquee Section */}
      <LogoMarquee />

      {/* Features Section - Interactive Demo */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20 md:py-32">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            See it in action
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-[var(--text-primary)] mb-4">
            From question to <span className="text-gradient">perfect match</span><br />
            in seconds
          </h2>
          <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
            Watch how Nestfinder understands what you need and finds apartments that actually fit
          </p>
        </div>

        {/* Live Demo */}
        <div className="max-w-4xl mx-auto mb-20">
          <LiveDemo />
        </div>

        {/* Search Transformation - Visual Input/Output */}
        <div className="mb-28">
          {/* Giant search input visualization */}
          <div className="relative max-w-4xl mx-auto">
            {/* Static sticker tags - pasted ON the container edges */}
            <div className="hidden lg:block absolute left-4 -top-3 px-4 py-2 rounded-xl bg-emerald-100 dark:bg-emerald-900/40 text-sm font-medium text-emerald-700 dark:text-emerald-300 -rotate-3 shadow-md z-10 border border-emerald-200 dark:border-emerald-800">
              near downtown
            </div>
            <div className="hidden lg:block absolute right-8 -top-3 px-4 py-2 rounded-xl bg-amber-100 dark:bg-amber-900/40 text-sm font-medium text-amber-700 dark:text-amber-300 rotate-2 shadow-md z-10 border border-amber-200 dark:border-amber-800">
              under $2000
            </div>
            <div className="hidden lg:block absolute -left-3 bottom-20 px-4 py-2 rounded-xl bg-blue-100 dark:bg-blue-900/40 text-sm font-medium text-blue-700 dark:text-blue-300 -rotate-6 shadow-md z-10 border border-blue-200 dark:border-blue-800">
              safe area
            </div>
            <div className="hidden lg:block absolute -right-3 bottom-16 px-4 py-2 rounded-xl bg-pink-100 dark:bg-pink-900/40 text-sm font-medium text-pink-700 dark:text-pink-300 rotate-6 shadow-md z-10 border border-pink-200 dark:border-pink-800">
              pet-friendly
            </div>
            
            {/* The "input" area */}
            <div className="relative rounded-3xl bg-gradient-to-br from-[var(--bg-secondary)] to-[var(--bg-tertiary)] border border-[var(--border-color)] p-8 md:p-12 shadow-2xl overflow-hidden">
              {/* Background glow */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/10 rounded-full blur-3xl" />
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-[var(--accent)]/5 rounded-full blur-2xl" />
              
              <div className="relative">
                {/* Input label */}
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-3 h-3 rounded-full bg-[var(--accent)] animate-pulse" />
                  <span className="text-sm font-medium text-[var(--text-muted)] uppercase tracking-wider">Ask anything</span>
                </div>
                
                {/* Fake input with rotating examples */}
                <div className="text-2xl md:text-3xl font-medium text-[var(--text-primary)] mb-8 min-h-[80px]">
                  "1BR under $1800, close to uOttawa, pet-friendly with parking"
                </div>
                
                {/* Divider with arrow */}
                <div className="flex items-center gap-4 my-8">
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--border-color)] to-transparent" />
                  <div className="w-12 h-12 rounded-full bg-[var(--accent)] flex items-center justify-center shadow-lg shadow-[var(--accent)]/25">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                      <path d="M12 5v14M5 12l7 7 7-7" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--border-color)] to-transparent" />
                </div>
                
                {/* Output cards */}
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="group p-5 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border-color)] hover:border-[var(--accent)]/50 transition-all">
                    <div className="text-4xl font-bold text-[var(--accent)] mb-2">14</div>
                    <div className="text-sm text-[var(--text-primary)] font-medium">Perfect matches</div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">from 160+ listings</div>
                  </div>
                  
                  <div className="group p-5 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border-color)] hover:border-[var(--accent)]/50 transition-all">
                    <div className="text-4xl font-bold text-[var(--accent)] mb-2">8-15</div>
                    <div className="text-sm text-[var(--text-primary)] font-medium">Min commute</div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">to your pinned spot</div>
                  </div>
                  
                  <div className="group p-5 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border-color)] hover:border-[var(--accent)]/50 transition-all">
                    <div className="text-4xl font-bold text-[var(--accent)] mb-2">A+</div>
                    <div className="text-sm text-[var(--text-primary)] font-medium">Safety rated</div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">walkability included</div>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        </div>

        {/* The Journey - Vertical Timeline with Moving Dot */}
        <TimelineWithMovingDot />
      </section>


      {/* Footer */}
      <footer className="border-t border-[var(--border-color)] bg-[var(--bg-primary)]">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-[var(--text-secondary)]">
              © 2026 Nestfinder. All rights reserved.
            </p>
            <div className="flex items-center gap-3">
              <ThemeTogglePill />
              <a
                href="https://github.com/Homeless-Gonnabe-5-0/Nestfinder"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-all duration-200"
                aria-label="View on GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
