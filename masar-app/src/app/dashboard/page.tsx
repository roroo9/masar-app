"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  Menu,
  Bell,
  CheckCircle2,
  Star,
  Zap,
  TrendingUp,
  Home,
  BookOpen,
  UserRound,
  Lightbulb,
  Calendar,
} from "lucide-react";
import {
  getStudentId,
  getDashboard,
  getReadiness,
  getStudentSkills,
  type DashboardResponse,
  type ReadinessResponse,
  type StudentSkillsResponse,
} from "@/lib/api";
import { EmptyState, ErrorState, LoadingSpinner } from "@/lib/states";

function Logo() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 22 22"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        d="M4 18 L4 4 L18 4"
        stroke="#5D3FD3"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ProgressRing({ value }: { value: number }) {
  const r = 64;
  const c = 2 * Math.PI * r;
  const visible = (value / 100) * c;
  const gap = c - visible;

  return (
    <svg
      width="160"
      height="160"
      viewBox="0 0 160 160"
      className="-rotate-90"
      aria-hidden
    >
      <circle
        cx="80"
        cy="80"
        r={r}
        stroke="rgba(255,255,255,0.20)"
        strokeWidth="10"
        fill="none"
      />
      <circle
        cx="80"
        cy="80"
        r={r}
        stroke="white"
        strokeWidth="10"
        fill="none"
        strokeDasharray={`${visible} ${gap}`}
        strokeLinecap="round"
      />
    </svg>
  );
}

function BottomNav() {
  const items = [
    { href: "/dashboard", label: "الرئيسية", icon: Home, active: true },
    { href: "/skills", label: "المهارات", icon: BookOpen },
    { href: "/recommended", label: "الفرص", icon: Lightbulb },
    { href: "/plan", label: "الخطة", icon: Calendar },
    { href: "/profile", label: "ملفي", icon: UserRound },
  ];
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 mx-auto w-full max-w-[390px] border-t border-black/[0.06] bg-white">
      <ul className="grid grid-cols-5 px-2 pb-3 pt-2">
        {items.map((it) => {
          const Icon = it.icon;
          return (
            <li key={it.label}>
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

function firstName(fullName: string): string {
  return fullName.trim().split(/\s+/)[0] ?? fullName;
}

function firstLetter(name: string): string {
  const trimmed = name.trim();
  return trimmed ? trimmed[0] : "م";
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [skills, setSkills] = useState<StudentSkillsResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");

  const fetchAll = useCallback(async () => {
    try {
      const sid = getStudentId();
      const [d, s] = await Promise.all([
        getDashboard(sid),
        getStudentSkills(sid),
      ]);
      setDashboard(d);
      setSkills(s);

      const topJobId = d.top_scores[0]?.job_id ?? d.jobs[0]?.job_id;
      if (topJobId != null) {
        try {
          const r = await getReadiness(sid, topJobId);
          setReadiness(r);
        } catch {
          setReadiness(null);
        }
      }
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  const retry = useCallback(() => {
    setStatus("loading");
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchAll();
  }, [fetchAll]);

  return (
    <div className="min-h-screen bg-canvas pb-24">
      <header className="flex items-center justify-between px-5 pt-5 pb-3">
        <button aria-label="القائمة" className="text-text/80 active:text-primary">
          <Menu size={24} strokeWidth={1.75} />
        </button>

        <div className="flex items-center gap-2">
          <span className="text-[18px] font-bold tracking-tight text-text">
            مسار
          </span>
          <Logo />
        </div>

        <div className="flex items-center gap-3">
          <button aria-label="الإشعارات" className="text-text/80">
            <Bell size={22} strokeWidth={1.75} />
          </button>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-purple-light">
            <span className="text-[15px] font-semibold text-primary">
              {dashboard ? firstLetter(dashboard.student.name) : "م"}
            </span>
          </div>
        </div>
      </header>

      {status === "loading" && <LoadingSpinner />}
      {status === "error" && <ErrorState onRetry={retry} />}

      {status === "ready" && dashboard && (
        <>
          <section className="px-5 pt-3 pb-5">
            <h1 className="text-[22px] font-bold tracking-tight text-text">
              مرحباً {firstName(dashboard.student.name)}
            </h1>
            <p className="mt-1 text-[13.5px] text-muted">
              جاهز لمراجعة تقدمك اليوم؟
            </p>
          </section>

          <section className="px-5">
            <div className="rounded-2xl bg-primary p-5 text-white shadow-[0_10px_30px_-12px_rgba(93,63,211,0.45)]">
              {dashboard.top_scores.length > 0 ? (
                <>
                  <div className="flex justify-center pt-1">
                    <div className="relative">
                      <ProgressRing value={dashboard.top_scores[0].score} />
                      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                        <span className="text-[34px] font-bold tracking-tight">
                          {Math.round(dashboard.top_scores[0].score)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="mt-4 text-center text-[16px] font-bold leading-snug">
                    أنت جاهز بنسبة {Math.round(dashboard.top_scores[0].score)}%
                    لوظيفة {dashboard.top_scores[0].title}
                  </p>
                  <p className="mx-auto mt-2 max-w-[280px] text-center text-[12.5px] leading-relaxed text-white/85">
                    أنت على الطريق الصحيح، واصل تطوير مهاراتك في المجالات
                    المتبقية للوصول إلى الجاهزية الكاملة
                  </p>
                </>
              ) : (
                <div className="py-6 text-center text-[13.5px] text-white/90">
                  لا توجد بيانات جاهزية بعد
                </div>
              )}

              <Link
                href="/plan"
                className="mt-4 block w-full rounded-xl bg-white/15 py-3 text-center text-[14px] font-semibold text-white transition-colors hover:bg-white/20 active:bg-white/25"
              >
                عرض التفاصيل ←
              </Link>
            </div>
          </section>

          <section className="mt-5 px-5">
            <h2 className="mb-3 text-[15px] font-bold text-text">نظرة سريعة</h2>
            <div className="grid grid-cols-3 gap-2.5">
              <div className="rounded-xl border border-black/[0.06] bg-white p-3 text-center">
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center">
                  <CheckCircle2
                    size={20}
                    className="text-emerald-600"
                    strokeWidth={2}
                  />
                </div>
                <p className="text-[11.5px] leading-tight text-muted">
                  المهارات المؤكدة
                </p>
                <p className="mt-1 text-[22px] font-bold text-text">
                  {skills?.total_skills ?? dashboard.total_skills}
                </p>
              </div>

              <div className="rounded-xl border border-black/[0.06] bg-white p-3 text-center">
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center">
                  <Star
                    size={20}
                    className="text-primary"
                    strokeWidth={2}
                    fill="currentColor"
                  />
                </div>
                <p className="text-[11.5px] leading-tight text-muted">
                  الموصى بها
                </p>
                <p className="mt-1 text-[22px] font-bold text-text">
                  {readiness?.missing_skills.length ?? 0}
                </p>
              </div>

              <div className="rounded-xl border border-black/[0.06] bg-white p-3 text-center">
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center">
                  <Zap
                    size={20}
                    className="text-primary"
                    strokeWidth={2}
                    fill="currentColor"
                  />
                </div>
                <p className="text-[11.5px] leading-tight text-muted">
                  المهارات المطابقة
                </p>
                <p className="mt-1 text-[22px] font-bold text-text">
                  {readiness?.matched_skills.length ?? 0}
                </p>
              </div>
            </div>
          </section>

          <section className="mt-5 px-5">
            {readiness?.explanation &&
            "improvement_areas" in readiness.explanation &&
            readiness.explanation.improvement_areas.length > 0 ? (
              <div className="rounded-xl bg-purple-light p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white">
                      <TrendingUp
                        size={18}
                        className="text-primary"
                        strokeWidth={2.25}
                      />
                    </div>
                    <div>
                      <p className="text-[11.5px] font-medium text-muted">
                        الخطوة التالية
                      </p>
                      <p className="text-[16px] font-bold leading-tight text-text">
                        تعلم {readiness.explanation.improvement_areas[0].skill}
                      </p>
                    </div>
                  </div>
                </div>

                <p className="mt-3 text-[12px] text-muted">
                  أولوية: عالية · مدة مقترحة:{" "}
                  {readiness.explanation.improvement_areas[0].time_estimate}
                </p>

                <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white">
                  <div className="h-full w-0 rounded-full bg-primary" />
                </div>

                <Link
                  href="/plan"
                  className="mt-3 block w-full rounded-lg bg-primary py-2.5 text-center text-[13.5px] font-semibold text-white active:bg-primary/90"
                >
                  ابدأ الآن
                </Link>
              </div>
            ) : (
              <EmptyState />
            )}
          </section>
        </>
      )}

      <BottomNav />
    </div>
  );
}
