"use client";

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-10">
      <div
        className="h-7 w-7 animate-spin rounded-full border-[3px] border-purple-light border-t-primary"
        aria-label="جاري التحميل"
      />
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <p className="text-[13px] text-muted">حدث خطأ، حاول مجدداً</p>
      <button
        onClick={onRetry}
        className="rounded-lg border border-primary bg-white px-4 py-2 text-[12.5px] font-semibold text-primary active:bg-purple-subtle"
      >
        إعادة المحاولة
      </button>
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="flex items-center justify-center py-8">
      <p className="text-[13px] text-muted">لا توجد بيانات</p>
    </div>
  );
}
