'use client';

import Image from 'next/image';

const websites = [
  { 
    name: 'Kijiji', 
    logo: '/logos/1768678537-trimmy-kijiji_logo.png',
    url: 'https://www.kijiji.ca',
  },
  { 
    name: 'Zumper', 
    logo: '/logos/Zumper_Logo-removebg-preview.png',
    url: 'https://www.zumper.com',
  },
  { 
    name: 'Zillow', 
    logo: '/logos/Zillow-Logo-removebg-preview.png',
    url: 'https://www.zillow.com',
  },
  { 
    name: 'Rentals.ca', 
    logo: '/logos/rentals.ca_logo.png',
    url: 'https://www.rentals.ca',
  },
];

// Create a longer array by repeating logos for a fuller marquee
const marqueeItems = [...websites, ...websites, ...websites, ...websites];

function LogoItem({ site }: { site: typeof websites[0] }) {
  return (
    <a 
      href={site.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex-shrink-0 flex items-center justify-center px-8 md:px-12"
    >
      <div className="transition-all duration-300 ease-out opacity-70 hover:opacity-100">
        <Image
          src={site.logo}
          alt={`${site.name} logo`}
          width={120}
          height={48}
          className="h-10 md:h-12 w-auto object-contain grayscale hover:grayscale-0 transition-all duration-300 mix-blend-multiply dark:mix-blend-screen dark:invert"
        />
      </div>
    </a>
  );
}

export default function LogoMarquee() {
  return (
    <section className="max-w-7xl mx-auto px-6 lg:px-8 py-16 md:py-20">
      <div className="text-center mb-12">
        <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)] mb-3">
          Scrapes data from websites like:
        </h2>
        <p className="text-sm md:text-base text-[var(--text-secondary)]">
          We aggregate listings from multiple sources to give you the complete picture
        </p>
      </div>

      {/* Marquee Container */}
      <div className="relative overflow-hidden py-4">
        {/* Left Fade */}
        <div className="absolute left-0 top-0 bottom-0 w-24 md:w-40 bg-gradient-to-r from-[var(--bg-primary)] to-transparent z-10 pointer-events-none" />
        
        {/* Right Fade */}
        <div className="absolute right-0 top-0 bottom-0 w-24 md:w-40 bg-gradient-to-l from-[var(--bg-primary)] to-transparent z-10 pointer-events-none" />

        {/* Scrolling Content - Two identical tracks for seamless loop */}
        <div className="flex animate-marquee">
          {/* First track */}
          <div className="flex shrink-0">
            {marqueeItems.map((site, index) => (
              <LogoItem key={`track1-${index}`} site={site} />
            ))}
          </div>
          {/* Second track (duplicate for seamless loop) */}
          <div className="flex shrink-0">
            {marqueeItems.map((site, index) => (
              <LogoItem key={`track2-${index}`} site={site} />
            ))}
          </div>
        </div>
      </div>

      {/* Additional info text */}
      <div className="text-center mt-8">
        <p className="text-xs text-[var(--text-muted)]">
          Real-time data aggregation from Ottawa's top rental platforms
        </p>
      </div>
    </section>
  );
}
