"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";
import { setAuth } from "@/lib/auth";

function Logo() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <path d="M4 18 L4 4 L18 4" stroke="#5D3FD3" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      setAuth(res.token, res.student_id);
      router.replace("/dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '';
      if (msg.includes('401')) {
        setError("البريد الإلكتروني أو كلمة المرور غير صحيحة");
      } else if (msg.includes('404') || msg.includes('400')) {
        setError("هذا البريد الإلكتروني غير مسجل — أنشئ حساباً جديداً");
      } else {
        setError("تعذر الاتصال بالخادم، تحقق من اتصالك وحاول مجدداً");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-canvas px-5">
      <header className="flex items-center justify-center gap-2 pt-12 pb-10">
        <span className="text-[20px] font-bold tracking-tight text-text">مسار</span>
        <Logo />
      </header>

      <div className="mb-7">
        <h1 className="text-[24px] font-bold text-text">مرحباً بعودتك</h1>
        <p className="mt-1.5 text-[14px] text-muted">سجّل دخولك لمتابعة رحلتك المهنية</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-2 block text-[13.5px] font-semibold text-text">
            البريد الإلكتروني
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="example@university.edu.sa"
            dir="ltr"
            required
            className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <div>
          <label className="mb-2 block text-[13.5px] font-semibold text-text">
            كلمة المرور
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            dir="ltr"
            required
            className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>

        {error && (
          <p className="rounded-xl bg-red-50 px-4 py-3 text-right text-[13px] font-semibold text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !email || !password}
          className="mt-2 w-full rounded-xl bg-primary py-4 text-[15px] font-bold text-white disabled:opacity-35 active:bg-primary/90"
        >
          {loading ? "جاري الدخول..." : "تسجيل الدخول ←"}
        </button>
      </form>

      <p className="mt-6 text-center text-[13.5px] text-muted">
        ليس لديك حساب؟{" "}
        <Link href="/onboarding" className="font-semibold text-primary">
          سجّل الآن
        </Link>
      </p>
    </div>
  );
}
