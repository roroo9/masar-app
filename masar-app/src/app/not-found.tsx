"use client";

import Link from "next/link";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-canvas px-6 text-center">
      <p className="text-6xl font-bold text-primary">404</p>
      <h1 className="mt-4 text-[18px] font-bold text-text">الصفحة غير موجودة</h1>
      <p className="mt-2 text-[13px] text-muted">تأكد من الرابط أو عد للرئيسية</p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-[14px] font-semibold text-white"
      >
        <Home size={16} strokeWidth={2} />
        الرئيسية
      </Link>
    </div>
  );
}
