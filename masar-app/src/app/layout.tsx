import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "مسار",
  description: "محرّك تحليلات المهارات لطلبة الجامعات السعودية",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen bg-canvas text-text">
        <div className="mx-auto w-full max-w-[390px] min-h-screen bg-canvas">
          {children}
        </div>
      </body>
    </html>
  );
}
