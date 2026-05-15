"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ChevronLeft,
  ChevronDown,
  Info,
  Star,
  CheckCircle2,
  Home,
  BookOpen,
  UserRound,
  Lightbulb,
  Calendar,
} from "lucide-react";
import {
  getStudentId,
  getAllJobs,
  getDashboard,
  getReadiness,
  getStudentSkills,
  getTopDemandedSkills,
  type ReadinessResponse,
  type TopDemandedSkill,
} from "@/lib/api";
import { EmptyState, ErrorState, LoadingSpinner } from "@/lib/states";

function BottomNav() {
  const items = [
    { href: "/dashboard", label: "الرئيسية", icon: Home },
    { href: "/skills", label: "المهارات", icon: BookOpen },
    { href: "/recommended", label: "الفرص", icon: Lightbulb, active: true },
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

type Opportunity = {
  name: string;
  duration: string;
  signal: string;
};

function categoryArabic(category: string): string {
  const c = category.toLowerCase();
  if (c.includes("soft")) return "المهارات الشخصية";
  if (c.includes("domain")) return "المجال التخصصي";
  return "المهارات التقنية";
}

function durationFor(estimate: string | undefined, category: string): string {
  if (estimate && estimate.trim()) return estimate;
  const c = category.toLowerCase();
  if (c.includes("soft")) return "أسبوعان";
  if (c.includes("domain")) return "4 أسابيع";
  return "3 أسابيع";
}

function buildOpportunities(
  readiness: ReadinessResponse | null,
  topDemanded: TopDemandedSkill[],
  ownedNames: Set<string>,
  totalJobs: number,
): Opportunity[] {
  const improvements =
    readiness?.explanation &&
    "improvement_areas" in readiness.explanation
      ? readiness.explanation.improvement_areas
      : [];

  const fromImprovements: Opportunity[] = improvements.map((a) => ({
    name: a.skill,
    duration: durationFor(a.time_estimate, ""),
    signal: a.why_it_matters,
  }));

  const seen = new Set<string>(
    fromImprovements.map((o) => o.name.toLowerCase()),
  );

  const fromMarket: Opportunity[] = topDemanded
    .filter((s) => !ownedNames.has(s.name.toLowerCase()))
    .filter((s) => !seen.has(s.name.toLowerCase()))
    .slice(0, 12)
    .map((s) => {
      const pct = totalJobs > 0
        ? Math.min(99, Math.round((s.job_demand / totalJobs) * 100))
        : 0;
      const segment = categoryArabic(s.category);
      const signal = pct > 0
        ? `تظهر في ${pct}% من ${segment}`
        : `مطلوبة في ${s.job_demand} وظيفة`;
      return {
        name: s.name,
        duration: durationFor(undefined, s.category),
        signal,
      };
    });

  return [...fromImprovements, ...fromMarket].slice(0, 10);
}

function usePlan() {
  const [plan, setPlan] = useState<Set<string>>(new Set());

  useEffect(() => {
    try {
      const stored = localStorage.getItem("masar_plan");
      if (stored) setPlan(new Set(JSON.parse(stored) as string[]));
    } catch { /* ignore */ }
  }, []);

  function toggle(skillName: string) {
    setPlan((prev) => {
      const next = new Set(prev);
      if (next.has(skillName)) {
        next.delete(skillName);
      } else {
        next.add(skillName);
      }
      localStorage.setItem("masar_plan", JSON.stringify([...next]));
      return next;
    });
  }

  return { plan, toggle };
}

export default function RecommendedPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[] | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const { plan, toggle } = usePlan();

  const fetchAll = useCallback(async () => {
    try {
      const sid = getStudentId();
      const [dashboard, studentSkills, topDemanded, jobs] = await Promise.all([
        getDashboard(sid),
        getStudentSkills(sid),
        getTopDemandedSkills(),
        getAllJobs(),
      ]);

      const owned = new Set<string>([
        ...studentSkills.technical.map((s) => s.name.toLowerCase()),
        ...studentSkills.soft.map((s) => s.name.toLowerCase()),
        ...studentSkills.domain.map((s) => s.name.toLowerCase()),
      ]);

      const topJobId = dashboard.top_scores[0]?.job_id ?? dashboard.jobs[0]?.job_id;
      let readiness: ReadinessResponse | null = null;
      if (topJobId != null) {
        try {
          readiness = await getReadiness(sid, topJobId);
        } catch {
          readiness = null;
        }
      }

      setOpportunities(
        buildOpportunities(readiness, topDemanded.top_skills, owned, jobs.total),
      );
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

  const count = opportunities?.length ?? 0;

  return (
    <div className="min-h-screen bg-canvas pb-24">
      <header className="flex items-center justify-between px-5 pt-5 pb-4">
        <Link href="/dashboard" aria-label="رجوع" className="text-text/80">
          <ChevronLeft size={24} strokeWidth={2} />
        </Link>
        <div className="flex items-center gap-2">
          <Star
            size={18}
            className="text-primary"
            strokeWidth={2}
            fill="currentColor"
          />
          <h1 className="text-[17px] font-bold text-text">
            المهارات الموصى بها
          </h1>
        </div>
        <span className="w-6" aria-hidden />
      </header>

      <div className="border-b border-black/[0.08] px-5">
        <div className="flex items-center gap-6">
          <button className="py-3 text-[13.5px] font-medium text-muted">
            الكل
          </button>
          <Link
            href="/skills"
            className="py-3 text-[13.5px] font-medium text-muted"
          >
            المؤكدة
          </Link>
          <button className="relative flex items-center gap-1.5 py-3 text-[13.5px] font-bold text-primary">
            <span>الموصى بها</span>
            <span className="rounded-full bg-purple-light px-1.5 py-0.5 text-[10.5px] font-semibold text-primary">
              {count}
            </span>
            <span className="absolute inset-x-0 -bottom-px h-[2.5px] rounded-t bg-primary" />
          </button>
        </div>
      </div>

      <section className="px-5 pt-4">
        <div className="flex items-center justify-between rounded-xl border border-black/[0.06] bg-white px-3 py-2.5">
          <div className="flex items-center gap-1.5 text-[13.5px] font-medium text-text">
            <span>الأكثر طلباً في السوق</span>
            <ChevronDown size={16} strokeWidth={2} />
          </div>
          <button aria-label="معلومات" className="text-muted">
            <Info size={18} strokeWidth={1.75} />
          </button>
        </div>
      </section>

      <section className="px-5 pt-5 pb-3">
        <h2 className="text-[16px] font-bold text-text">فرص نمو لك ({count})</h2>
        <p className="mt-1 text-[12.5px] text-muted">
          مهارات ترفع قيمتك في السوق إذا أضفتها
        </p>
      </section>

      {status === "loading" && <LoadingSpinner />}
      {status === "error" && <ErrorState onRetry={retry} />}

      {status === "ready" && opportunities && opportunities.length === 0 && (
        <EmptyState />
      )}

      {status === "ready" && opportunities && opportunities.length > 0 && (
        <section className="space-y-2.5 px-5">
          {opportunities.map((o, idx) => (
            <article
              key={`${o.name}-${idx}`}
              className="rounded-xl border bg-white p-4"
              style={{ borderColor: "rgba(93,63,211,0.15)" }}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="rounded-full bg-purple-light px-2.5 py-1 text-[11.5px] font-semibold text-primary">
                  {o.duration}
                </span>
                <h3 className="text-[16.5px] font-bold text-text">{o.name}</h3>
              </div>

              <div className="mt-3 rounded-lg bg-purple-subtle px-3 py-2.5 text-right text-[12.5px] font-medium text-primary">
                {o.signal}
              </div>

              <div className="mt-3 flex justify-end">
                {plan.has(o.name) ? (
                  <button
                    onClick={() => toggle(o.name)}
                    className="flex items-center gap-1.5 rounded-lg border border-emerald-500 bg-white px-4 py-2 text-[13px] font-semibold text-emerald-600 active:bg-emerald-50"
                  >
                    <CheckCircle2 size={15} strokeWidth={2.25} />
                    تمت الإضافة
                  </button>
                ) : (
                  <button
                    onClick={() => toggle(o.name)}
                    className="rounded-lg border border-primary bg-white px-4 py-2 text-[13px] font-semibold text-primary active:bg-purple-subtle"
                  >
                    + أضف للخطة
                  </button>
                )}
              </div>
            </article>
          ))}
        </section>
      )}

      <BottomNav />
    </div>
  );
}
