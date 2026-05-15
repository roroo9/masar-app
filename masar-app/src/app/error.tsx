"use client";

import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-canvas px-6 text-center">
      <p className="text-5xl">⚠️</p>
      <h1 className="mt-4 text-[18px] font-bold text-text">حدث خطأ غير متوقع</h1>
      <p className="mt-2 text-[13px] text-muted">نعتذر، يرجى المحاولة مرة أخرى</p>
      <button
        onClick={reset}
        className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-[14px] font-semibold text-white"
      >
        <RefreshCw size={16} strokeWidth={2} />
        إعادة المحاولة
      </button>
    </div>
  );
}
