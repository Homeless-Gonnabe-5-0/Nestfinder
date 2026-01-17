'use client';

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";
import ThemeTogglePill from "./components/ThemeTogglePill";
import LogoMarquee from "./components/LogoMarquee";
import { MapPin, Clock, Shield, DollarSign, TrendingUp, CheckCircle } from "lucide-react";

export default function Home() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  const features = [
    {
      icon: MapPin,
      title: "Smart Location Analysis",
      description: "Evaluate neighborhoods based on walkability, amenities, and local attractions."
    },
    {
      icon: Clock,
      title: "Commute Calculator",
      description: "Calculate accurate commute times to your workplace via transit, driving, or walking."
    },
    {
      icon: Shield,
      title: "Safety Scores",
      description: "View crime statistics and safety ratings for every neighborhood in Ottawa."
    },
    {
      icon: DollarSign,
      title: "Budget Optimizer",
      description: "Find the best value rentals that fit your budget and lifestyle needs."
    },
    {
      icon: TrendingUp,
      title: "Smart Ranking",
      description: "Our AI ranks apartments based on what matters most to you."
    },
    {
      icon: CheckCircle,
      title: "Real-Time Listings",
      description: "Access the latest apartment listings updated daily from multiple sources."
    }
  ];

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

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20 md:py-32">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-[var(--text-primary)] mb-4">
            Everything you need to find your perfect home
          </h2>
          <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
            Powerful features designed to make apartment hunting effortless and accurate
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="group p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:shadow-glow-card transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-[var(--accent-light)] flex items-center justify-center mb-4 transition-all duration-300 group-hover:bg-[var(--accent)] group-hover:shadow-glow-icon">
                <feature.icon className="w-6 h-6 text-[var(--accent)] group-hover:text-white transition-colors duration-300" strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">{feature.title}</h3>
              <p className="text-[var(--text-secondary)]">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>


      {/* Footer */}
      <footer className="border-t border-[var(--border-color)] bg-[var(--bg-primary)]">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-[var(--text-secondary)]">
              © 2026 Nestfinder. All rights reserved.
            </p>
            <ThemeTogglePill />
          </div>
        </div>
      </footer>
    </div>
  );
}
