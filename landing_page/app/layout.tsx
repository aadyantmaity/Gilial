import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Geist_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import SoftAurora from "@/components/SoftAurora";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Gilial",
  description:
    "Intelligently compress your Pinecone vector database. Remove low-scoring vectors to reduce storage costs while maintaining search quality.",
  themeColor: "#ffffff",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} ${spaceGrotesk.variable} ${geistMono.variable}`}>
      <body className={inter.className}>
        <div className="aurora-background">
          <SoftAurora
            speed={0.8}
            scale={3.5}
            brightness={0.65}
            color1="#3c6e71"
            color2="#6dafb4"
            noiseFrequency={2}
            noiseAmplitude={0.8}
            bandHeight={0.6}
            bandSpread={1.2}
            octaveDecay={0.15}
            layerOffset={0.5}
            colorSpeed={0.8}
            enableMouseInteraction={false}
          />
        </div>
        {children}
      </body>
    </html>
  );
}
