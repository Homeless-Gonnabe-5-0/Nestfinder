import type { Metadata } from "next";
import "./globals.css";
import { JetBrains_Mono } from "next/font/google";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Nestfinder - Find the best apartments in Ottawa",
  description: "Nestfinder ranks rentals by commute, safety, walkability, and price based on your priorities.",
  icons: {
    icon: "/images/1768631233-trimmy-Nestfinder logo.png",
    apple: "/images/1768631233-trimmy-Nestfinder logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={jetbrainsMono.variable}>
      <body className="antialiased bg-[var(--bg-primary)] text-[var(--text-primary)] font-mono font-medium">
        {children}
      </body>
    </html>
  );
}
