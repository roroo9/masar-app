import type { Metadata } from "next";
import "./globals.css";
import AuthProvider from "@/components/auth-provider";

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
          <AuthProvider>{children}</AuthProvider>
        </div>
      </body>
    </html>
  );
}
