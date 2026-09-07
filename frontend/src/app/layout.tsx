import "./globals.css";
import type { Metadata } from "next";
import { Sidebar } from "@/components/shared/Sidebar";
import { Navbar } from "@/components/shared/Navbar";

export const metadata: Metadata = {
  title: "MetroFlow | AI Platform for Metro Crowd Management & Scheduling",
  description: "AI-powered public transit intelligence system for metro crowd density tracking, demand forecasting, and dynamic scheduling.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f17] text-slate-100 min-h-screen flex antialiased">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Navbar />
          <main className="flex-1 p-6 overflow-y-auto bg-[#0b0f17]">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
