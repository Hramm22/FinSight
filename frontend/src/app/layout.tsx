import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FinSight | Market Briefing",
  description:
    "시장 뉴스와 데이터를 정리해 오늘의 핵심 흐름을 전달하는 금융 브리핑 서비스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={geist.variable}>{children}</body>
    </html>
  );
}