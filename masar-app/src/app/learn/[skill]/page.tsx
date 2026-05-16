"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ChevronLeft,
  Play,
  BookOpen,
  Code,
  ExternalLink,
  Globe,
  Zap,
  CheckCircle,
} from "lucide-react";
import { getSkillResources, confirmSkill, getStudentId, type LearningResource } from "@/lib/api";
import { LoadingSpinner, ErrorState } from "@/lib/states";

const platformColor: Record<string, string> = {
  YouTube:       "bg-red-50 text-red-600",
  Coursera:      "bg-blue-50 text-blue-700",
  edX:           "bg-red-50 text-red-700",
  freeCodeCamp:  "bg-emerald-50 text-emerald-700",
  Kaggle:        "bg-cyan-50 text-cyan-700",
  "Official Docs": "bg-gray-100 text-gray-700",
  "W3Schools":   "bg-green-50 text-green-700",
};

const typeIcon = (type: LearningResource["type"]) => {
  switch (type) {
    case "video":    return <Play size={15} strokeWidth={2} />;
    case "course":   return <BookOpen size={15} strokeWidth={2} />;
    case "docs":     return <Code size={15} strokeWidth={2} />;
    case "practice": return <Zap size={15} strokeWidth={2} />;
  }
};

const typeLabel: Record<LearningResource["type"], string> = {
  video:    "فيديو",
  course:   "كورس",
  docs:     "توثيق",
  practice: "تمارين",
};

function ResourceCard({ res, rank }: { res: LearningResource; rank: number }) {
  const colorClass =
    platformColor[res.platform] ?? "bg-purple-light text-primary";

  return (
    <a
      href={res.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start gap-3 rounded-xl border border-black/[0.06] bg-white p-4 active:bg-gray-50"
    >
      {/* Rank badge */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-[12px] font-bold text-white">
        {rank}
      </div>

      <div className="flex-1 min-w-0">
        {/* Title */}
        <p className="text-right text-[15px] font-bold text-text leading-snug">
          {res.title}
        </p>

        {/* Meta row */}
        <div className="mt-1.5 flex flex-wrap items-center justify-end gap-1.5">
          {/* Duration */}
          <span className="text-[11.5px] text-muted">{res.duration}</span>

          {/* Language */}
          <span className="flex items-center gap-0.5 rounded-full bg-black/[0.05] px-2 py-0.5 text-[10.5px] font-medium text-muted">
            <Globe size={9} strokeWidth={2} />
            {res.language === "ar" ? "عربي" : "English"}
          </span>

          {/* Free badge */}
          {res.free && (
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10.5px] font-semibold text-emerald-700">
              مجاني
            </span>
          )}

          {/* Type */}
          <span className="flex items-center gap-1 rounded-full bg-purple-light px-2 py-0.5 text-[10.5px] font-semibold text-primary">
            {typeIcon(res.type)}
            {typeLabel[res.type]}
          </span>

          {/* Platform */}
          <span className={`rounded-full px-2 py-0.5 text-[10.5px] font-semibold ${colorClass}`}>
            {res.platform}
          </span>
        </div>
      </div>

      <ExternalLink size={15} className="mt-0.5 shrink-0 text-muted" strokeWidth={1.75} />
    </a>
  );
}

export default function LearnSkillPage() {
  const router = useRouter();
  const params = useParams<{ skill: string }>();
  const skill = decodeURIComponent(params.skill ?? "");

  const [resources, setResources] = useState<LearningResource[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [confirmState, setConfirmState] = useState<"idle" | "saving" | "done">("idle");

  const load = useCallback(async () => {
    try {
      const data = await getSkillResources(skill);
      setResources(data.resources);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, [skill]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleConfirm() {
    setConfirmState("saving");
    try {
      await confirmSkill(getStudentId(), skill);
      setConfirmState("done");
    } catch {
      setConfirmState("idle");
    }
  }

  const freeResources = resources.filter((r) => r.free);
  const paidResources = resources.filter((r) => !r.free);

  return (
    <div className="min-h-screen bg-canvas pb-28">
      <header className="flex items-center justify-between px-5 pt-5 pb-4">
        <button
          onClick={() => router.back()}
          aria-label="رجوع"
          className="text-text/80 active:text-primary"
        >
          <ChevronLeft size={24} strokeWidth={2} />
        </button>
        <div className="flex flex-col items-center">
          <p className="text-[12px] text-muted">تعلم مهارة</p>
          <h1 className="text-[17px] font-bold text-text">{skill}</h1>
        </div>
        <span className="w-6" aria-hidden />
      </header>

      {status === "loading" && <LoadingSpinner />}
      {status === "error" && <ErrorState onRetry={() => { setStatus("loading"); load(); }} />}

      {status === "ready" && (
        <div className="px-5 space-y-6 pt-2">
          {resources.length === 0 ? (
            <div className="rounded-xl border border-black/[0.06] bg-white p-6 text-center">
              <p className="text-[14px] text-muted">لم يتم العثور على مصادر لهذه المهارة</p>
            </div>
          ) : (
            <>
              {freeResources.length > 0 && (
                <section>
                  <div className="mb-3 flex items-center justify-between">
                    <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
                      {freeResources.length} مصادر
                    </span>
                    <h2 className="text-[15px] font-bold text-text">مصادر مجانية</h2>
                  </div>
                  <div className="space-y-2.5">
                    {freeResources.map((r, i) => (
                      <ResourceCard key={r.url} res={r} rank={i + 1} />
                    ))}
                  </div>
                </section>
              )}

              {paidResources.length > 0 && (
                <section>
                  <div className="mb-3 flex items-center justify-between">
                    <span className="rounded-full bg-black/[0.06] px-2.5 py-1 text-[11px] font-semibold text-muted">
                      {paidResources.length} مصادر
                    </span>
                    <h2 className="text-[15px] font-bold text-text">كورسات معتمدة</h2>
                  </div>
                  <div className="space-y-2.5">
                    {paidResources.map((r, i) => (
                      <ResourceCard key={r.url} res={r} rank={i + 1} />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      )}
      {/* Sticky confirm button */}
      <div className="fixed inset-x-0 bottom-0 z-20 mx-auto w-full max-w-[390px] border-t border-black/[0.06] bg-white px-5 pb-8 pt-4">
        {confirmState === "done" ? (
          <div className="flex items-center justify-center gap-2 rounded-xl bg-emerald-50 py-4">
            <CheckCircle size={20} className="text-emerald-600" strokeWidth={2} />
            <span className="text-[15px] font-bold text-emerald-700">
              تمت الإضافة إلى مهاراتك المؤكدة
            </span>
          </div>
        ) : (
          <button
            onClick={handleConfirm}
            disabled={confirmState === "saving"}
            className="w-full rounded-xl bg-primary py-4 text-[15px] font-bold text-white disabled:opacity-50 active:bg-primary/90"
          >
            {confirmState === "saving" ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                جاري الحفظ...
              </span>
            ) : (
              "✓ اكملت هذه المهارة"
            )}
          </button>
        )}
      </div>
    </div>
  );
}
