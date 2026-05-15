"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ChevronLeft,
  Calendar,
  TrendingUp,
  RefreshCw,
  X,
  Home,
  BookOpen,
  UserRound,
  Lightbulb,
  Clock,
} from "lucide-react";
import {
  getStudentId,
  getDashboard,
  getReadiness,
  getStudentProjects,
  type ImprovementArea,
  type ReadinessResponse,
  type Project,
} from "@/lib/api";
import { ErrorState } from "@/lib/states";

const NAV_ITEMS = [
  { href: "/dashboard", label: "الرئيسية", icon: Home, active: false },
  { href: "/skills", label: "المهارات", icon: BookOpen, active: false },
  { href: "/recommended", label: "الفرص", icon: Lightbulb, active: false },
  { href: "/plan", label: "الخطة", icon: Calendar, active: true },
  { href: "/profile", label: "ملفي", icon: UserRound, active: false },
];

function BottomNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 mx-auto w-full max-w-[390px] border-t border-black/[0.06] bg-white">
      <ul className="grid grid-cols-5 px-2 pb-3 pt-2">
        {NAV_ITEMS.map((it) => {
          const Icon = it.icon;
          return (
            <li key={it.href}>
              <Link
                href={it.href as never}
                className={`flex flex-col items-center gap-1 py-1.5 ${
                  it.active ? "text-primary" : "text-muted"
                }`}
              >
                <Icon
                  size={22}
                  strokeWidth={it.active ? 2.25 : 1.75}
                  fill={it.active ? "currentColor" : "none"}
                  fillOpacity={it.active ? 0.08 : 0}
                />
                <span className="text-[11px] font-medium">{it.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function PlanSkeleton() {
  return (
    <div className="animate-pulse px-5 pt-2 space-y-3">
      <div className="h-[130px] rounded-2xl bg-gray-200" />
      <div className="h-5 w-32 rounded bg-gray-200 mt-5" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-[108px] rounded-xl bg-gray-200" />
      ))}
      <div className="h-5 w-40 rounded bg-gray-200 mt-4" />
      {[1, 2].map((i) => (
        <div key={i} className="h-[128px] rounded-xl bg-gray-200" />
      ))}
    </div>
  );
}

function ExplanationSkeleton() {
  return (
    <div className="animate-pulse px-5 space-y-2.5">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-[108px] rounded-xl bg-gray-200" />
      ))}
    </div>
  );
}

type Step = ImprovementArea & { priorityLabel: string; isActive: boolean };

function priorityFor(index: number, total: number): string {
  if (index === 0) return "أولوية: عالية";
  if (index === total - 1 && total > 2) return "أولوية: متوسطة";
  return "أولوية: عالية";
}

function usePlan() {
  const [plan, setPlan] = useState<string[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("masar_plan");
      if (stored) setPlan(JSON.parse(stored) as string[]);
    } catch { /* ignore */ }
  }, []);

  function remove(skillName: string) {
    setPlan((prev) => {
      const next = prev.filter((s) => s !== skillName);
      localStorage.setItem("masar_plan", JSON.stringify(next));
      return next;
    });
  }

  return { plan, remove };
}

export default function PlanPage() {
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [explanationStatus, setExplanationStatus] = useState<"idle" | "loading" | "ready">("idle");
  const { plan, remove } = usePlan();

  const fetchAll = useCallback(async (force = false) => {
    try {
      const sid = getStudentId();
      const dashboard = await getDashboard(sid);
      const topJobId =
        dashboard.top_scores[0]?.job_id ?? dashboard.jobs[0]?.job_id;
      if (topJobId != null) {
        // Phase 1: score (no Claude) + projects — renders in <500ms
        const [r, p] = await Promise.all([
          getReadiness(sid, topJobId, force, false),
          getStudentProjects(sid, topJobId),
        ]);
        setReadiness(r);
        setProjects(p.projects);
        setStatus("ready");
        setIsRefreshing(false);
        // Phase 2: Claude explanation in background — skeleton until it arrives
        setExplanationStatus("loading");
        getReadiness(sid, topJobId, false, true)
          .then((full) => { setReadiness(full); setExplanationStatus("ready"); })
          .catch(() => setExplanationStatus("idle"));
      } else {
        setReadiness(null);
        setStatus("ready");
        setIsRefreshing(false);
      }
    } catch {
      setStatus("error");
      setIsRefreshing(false);
    }
  }, []);

  const retry = useCallback(() => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    setStatus("loading");
    fetchAll(true);
  }, [fetchAll, isRefreshing]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const current = readiness ? Math.round(readiness.score) : 0;
  const target = Math.min(99, current + 18);
  const full = 100;

  const improvements: ImprovementArea[] =
    readiness?.explanation && "improvement_areas" in readiness.explanation
      ? readiness.explanation.improvement_areas
      : [];

  const steps: Step[] = improvements.map((a, idx) => ({
    ...a,
    priorityLabel: priorityFor(idx, improvements.length),
    isActive: idx === 0,
  }));

  return (
    <div className="min-h-screen bg-canvas pb-24">
      <header className="flex items-center justify-between px-5 pt-5 pb-4">
        <Link href="/dashboard" aria-label="رجوع" className="text-text/80">
          <ChevronLeft size={24} strokeWidth={2} />
        </Link>
        <div className="flex items-center gap-2">
          <Calendar size={20} className="text-primary" strokeWidth={2.25} />
          <h1 className="text-[17px] font-bold text-text">خطة تطويرك</h1>
        </div>
        <span className="w-6" aria-hidden />
      </header>

      {status === "loading" && <PlanSkeleton />}
      {status === "error" && <ErrorState onRetry={retry} />}

      {status === "ready" && (
        <div className="animate-fade-in">
          <section className="px-5 pt-2">
            <div className="rounded-2xl bg-primary p-5 text-white">
              <h2 className="text-right text-[14.5px] font-bold">
                مسارك للوصول إلى الجاهزية 100%
              </h2>

              <div className="relative mt-7 flex items-start justify-between">
                <div className="absolute right-[8%] left-[8%] top-[14px] h-[2px] bg-white/30" />

                <div className="relative z-10 flex flex-1 flex-col items-center text-center">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[10.5px] font-bold text-primary">
                    {current}%
                  </div>
                  <p className="mt-2 text-[11.5px] font-semibold">الآن</p>
                  <p className="mt-0.5 text-[10.5px] text-white/75">أنت هنا</p>
                </div>

                <div className="relative z-10 flex flex-1 flex-col items-center text-center">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white/45 bg-primary text-[10.5px] font-semibold text-white/80">
                    {target}%
                  </div>
                  <p className="mt-2 text-[11.5px] font-medium text-white/85">
                    الهدف القريب
                  </p>
                </div>

                <div className="relative z-10 flex flex-1 flex-col items-center text-center">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white/45 bg-primary text-[10.5px] font-semibold text-white/80">
                    {full}%
                  </div>
                  <p className="mt-2 text-[11.5px] font-medium leading-tight text-white/85">
                    الجاهزية الكاملة
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="px-5 pt-6 pb-3">
            <h2 className="text-[16px] font-bold text-text">الخطوات القادمة</h2>
          </section>

          {explanationStatus === "loading" && steps.length === 0 ? (
            <ExplanationSkeleton />
          ) : steps.length === 0 ? (
            <div className="px-5 py-6 text-center">
              <p className="text-[14px] font-semibold text-text">لا توجد خطوات بعد</p>
              <p className="mt-1.5 text-[12.5px] text-muted">
                أضف مهارات من{" "}
                <Link href="/recommended" className="text-primary underline">
                  صفحة الفرص
                </Link>{" "}
                لتبدأ خطتك
              </p>
            </div>
          ) : (
            <section className="space-y-2.5 px-5">
              {steps.map((step, idx) => {
                const number = idx + 1;
                return step.isActive ? (
                  <article key={number} className="rounded-xl bg-purple-light p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-[12px] font-bold text-white">
                        {number}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <TrendingUp
                            size={18}
                            className="mt-0.5 text-primary"
                            strokeWidth={2.25}
                          />
                          <div className="flex-1">
                            <h3 className="text-right text-[15.5px] font-bold text-text">
                              تعلم {step.skill}
                            </h3>
                            <p className="text-right text-[11.5px] font-semibold text-primary">
                              {step.priorityLabel}
                            </p>
                          </div>
                        </div>
                        <p className="mt-2 text-right text-[12px] text-muted">
                          مدة مقترحة: {step.time_estimate}
                        </p>
                        <Link
                          href={`/learn/${encodeURIComponent(step.skill)}`}
                          className="mt-3 inline-block rounded-lg bg-primary px-4 py-2 text-[13px] font-semibold text-white active:bg-primary/90"
                        >
                          ابدأ الآن
                        </Link>
                      </div>
                    </div>
                  </article>
                ) : (
                  <article
                    key={number}
                    className="rounded-xl border border-primary/20 bg-white p-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-primary text-[12px] font-bold text-primary">
                        {number}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <TrendingUp
                            size={18}
                            className="mt-0.5 text-primary"
                            strokeWidth={1.75}
                          />
                          <div className="flex-1">
                            <h3 className="text-right text-[15.5px] font-bold text-text">
                              تعلم {step.skill}
                            </h3>
                            <p className="text-right text-[11.5px] text-muted">
                              {step.priorityLabel}
                            </p>
                          </div>
                        </div>
                        <p className="mt-2 text-right text-[12px] text-muted">
                          مدة مقترحة: {step.time_estimate}
                        </p>
                        <span className="mt-3 inline-block rounded-md bg-purple-subtle px-2.5 py-1 text-[11.5px] font-semibold text-primary">
                          قادم
                        </span>
                      </div>
                    </div>
                  </article>
                );
              })}
            </section>
          )}

          {plan.length > 0 && (
            <section className="mt-6 px-5">
              <h2 className="mb-3 text-[16px] font-bold text-text">
                مهاراتك المضافة يدوياً
              </h2>
              <div className="space-y-2">
                {plan.map((skillName) => (
                  <div
                    key={skillName}
                    className="flex items-center justify-between rounded-xl border border-black/[0.06] bg-white px-4 py-3"
                  >
                    <button
                      onClick={() => remove(skillName)}
                      aria-label="إزالة"
                      className="text-muted active:text-red-500"
                    >
                      <X size={16} strokeWidth={2} />
                    </button>
                    <span className="text-[14.5px] font-semibold text-text">{skillName}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {projects.length > 0 && (
            <section className="mt-6 px-5">
              <h2 className="mb-3 text-[16px] font-bold text-text">مشاريع مقترحة لك</h2>
              <div className="space-y-2.5">
                {projects.map((proj) => (
                  <article
                    key={proj.id}
                    className="rounded-xl border border-black/[0.06] bg-white p-4"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className={`shrink-0 rounded-full px-2.5 py-1 text-[10.5px] font-semibold ${
                        proj.difficulty === "beginner"
                          ? "bg-emerald-50 text-emerald-700"
                          : proj.difficulty === "advanced"
                          ? "bg-red-50 text-red-600"
                          : "bg-purple-light text-primary"
                      }`}>
                        {proj.difficulty === "beginner" ? "مبتدئ" : proj.difficulty === "advanced" ? "متقدم" : "متوسط"}
                      </span>
                      <div className="flex-1 text-right">
                        <h3 className="text-[15px] font-bold text-text leading-snug">{proj.title}</h3>
                        <p className="mt-0.5 text-[12px] text-muted">{proj.company}</p>
                      </div>
                    </div>
                    <p className="mt-2 text-right text-[12px] text-muted line-clamp-2">{proj.description}</p>
                    {(proj.skills_you_will_learn ?? []).length > 0 && (
                      <div className="mt-2.5 flex flex-wrap justify-end gap-1.5">
                        {(proj.skills_you_will_learn ?? []).slice(0, 4).map((s) => (
                          <span key={s} className="rounded-full bg-purple-light px-2 py-0.5 text-[10.5px] font-medium text-primary">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="mt-2.5 flex items-center justify-end gap-1 text-[11.5px] text-muted">
                      <Clock size={12} strokeWidth={2} />
                      <span>{proj.estimated_hours} ساعة</span>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          <section className="mt-5 px-5">
            <div className="rounded-xl bg-purple-light p-4">
              <h3 className="text-right text-[15px] font-bold text-text">
                هل تريد تحديث خطتك؟
              </h3>
              <p className="mt-1 text-right text-[12.5px] text-muted">
                يمكننا إعادة تحليل مهاراتك وتحديث الخطة حسب تقدمك
              </p>
              <div className="mt-3 flex justify-end">
                <button
                  onClick={retry}
                  disabled={isRefreshing}
                  className="inline-flex items-center gap-2 rounded-lg border border-primary bg-white px-4 py-2 text-[13px] font-semibold text-primary active:bg-purple-subtle disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  <RefreshCw
                    size={15}
                    strokeWidth={2.25}
                    className={isRefreshing ? "animate-spin" : ""}
                  />
                  {isRefreshing ? "جاري التحديث..." : "تحديث الخطة"}
                </button>
              </div>
            </div>
          </section>
        </div>
      )}

      <BottomNav />
    </div>
  );
}
