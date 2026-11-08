import type { Metadata } from "next";
import { Bebas_Neue, Inter } from "next/font/google";
import "./globals.css";

const bebas = Bebas_Neue({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-display",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-ui",
});

export const metadata: Metadata = {
  title: "Kuku Microdrama — Find the Promos | Vertical Short-Form Engine",
  description: "Automated promotional cutpoint discovery engine for vertical microdramas | I Married a Broken Soldier. He was a Duke",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${bebas.variable} ${inter.variable} bg-white text-[#111111]`}>
      <body className="bg-white text-[#111111] min-h-screen antialiased selection:bg-[#111111] selection:text-white font-[family-name:var(--font-ui)]">
        {children}
      </body>
    </html>
  );
}
