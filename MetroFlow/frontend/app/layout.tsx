import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MetroFlow",
  description: "AI-powered metro crowd management and ridership prediction",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}