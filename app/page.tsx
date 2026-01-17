'use client';

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";

export default function Home() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar Container */}
      <div className={`${isScrolled ? 'sticky top-4 px-4 lg:px-8' : ''} z-50 transition-all duration-500 ease-in-out ${!isScrolled ? 'border-b border-gray-200' : ''}`}>
        <nav className={`max-w-7xl mx-auto bg-white ${isScrolled ? 'rounded-2xl shadow-lg border border-gray-100' : ''} transition-all duration-500 ease-in-out`}>
          <div className="px-6 lg:px-8">
            <div className="flex items-center justify-between h-20">
              {/* Left: Logo + Text */}
              <div className="flex items-center gap-2">
                <Image 
                  src="/images/1768631233-trimmy-Nestfinder logo.png" 
                  alt="Nestfinder Logo" 
                  width={48}
                  height={48}
                  className="w-12 h-12 object-contain"
                  priority
                />
                <span className="text-xl font-bold tracking-[-0.02em] text-gray-900">Nestfinder</span>
              </div>

              {/* Right: CTA Buttons */}
              <div className="flex items-center gap-3">
                <button className="hidden sm:inline-flex items-center px-3 py-1.5 text-sm rounded-md border-2 border-[#1F4D2B] text-[#1F4D2B] font-medium hover:bg-[#1F4D2B] hover:text-white transition-all duration-200">
                  Try Demo
                </button>
                <Link
                  href="/chat"
                  className="inline-flex items-center px-3 py-1.5 text-sm rounded-md bg-[#1F4D2B] text-white font-medium hover:bg-opacity-90 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </nav>
      </div>

      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-6 lg:px-8 pt-16 pb-12 md:pt-24 md:pb-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 tracking-tight mb-6">
            Find the best apartments in Ottawa — fast.
          </h1>
          <p className="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto mb-12">
            NestFinder ranks rentals by commute, safety, walkability, and price based on your priorities.
          </p>
          
          {/* Placeholder for future visual */}
          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl h-96 flex items-center justify-center">
              <p className="text-gray-400 font-medium">Visual placeholder</p>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="max-w-5xl mx-auto px-6 lg:px-8 py-20 md:py-32">
        <div className="text-center">
          <p className="text-sm text-gray-500 font-medium uppercase tracking-wide mb-10">Built for Ottawa renters</p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="w-36 h-20 bg-gray-100 rounded-xl flex items-center justify-center transition-all hover:bg-gray-200"
              >
                <span className="text-gray-400 text-sm font-medium">Partner {i}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
