"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ChevronLeft,
  TrendingUp,
  Plus,
  Star,
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
  type StudentSkill,
  type StudentSkillsResponse,
  type ReadinessResponse,
} from "@/lib/api";
import { EmptyState, ErrorState, LoadingSpinner } from "@/lib/states";

function BottomNav() {
  const items = [
    { href: "/dashboard", label: "الرئيسية", icon: Home },
    { href: "/skills", label: "المهارات", icon: BookOpen, active: true },
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

function categoryLabel(category: "technical" | "soft" | "domain"): string {
  switch (category) {
    case "technical": return "مهارة تقنية · من مقرراتك";
    case "soft":      return "مهارة شخصية · من مقرراتك";
    case "domain":    return "مهارة تخصصية · من مقرراتك";
  }
}

type FlatSkill = StudentSkill & { category: "technical" | "soft" | "domain"; source?: string };

function flatten(skills: StudentSkillsResponse): FlatSkill[] {
  return [
    ...skills.technical.map((s) => ({ ...s, category: "technical" as const, source: s.source })),
    ...skills.domain.map((s) => ({ ...s, category: "domain" as const, source: s.source })),
    ...skills.soft.map((s) => ({ ...s, category: "soft" as const, source: s.source })),
  ];
}

function SkillCard({ skill }: { skill: FlatSkill }) {
  const isSelf = skill.source === "self_reported";
  return (
    <article
      className={`rounded-xl border p-4 ${
        isSelf
          ? "border-primary/20 bg-purple-subtle"
          : "border-black/[0.06] bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h3 className="text-right text-[16px] font-bold text-text">{skill.name}</h3>
          <p className="mt-0.5 text-right text-[12px] text-muted">
            {isSelf ? "اخترتها في التسجيل" : categoryLabel(skill.category)}
          </p>
        </div>
        {isSelf && (
          <span className="mt-0.5 flex shrink-0 items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10.5px] font-semibold text-primary">
            <Star size={10} fill="currentColor" strokeWidth={0} />
            مؤكدة
          </span>
        )}
      </div>
    </article>
  );
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<StudentSkillsResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [activeTab, setActiveTab] = useState<"confirmed" | "all">("confirmed");

  const fetchAll = useCallback(async () => {
    try {
      const sid = getStudentId();
      const [s, d] = await Promise.all([
        getStudentSkills(sid),
        getDashboard(sid),
      ]);
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

  const flat = skills ? flatten(skills) : [];
  const selfSkills = flat.filter((s) => s.source === "self_reported");
  const courseSkills = flat.filter((s) => s.source !== "self_reported");
  const recommendedCount = readiness?.missing_skills.length ?? 0;

  return (
    <div className="min-h-screen bg-canvas pb-24">
      <header className="flex items-center justify-between px-5 pt-5 pb-4">
        <Link href="/dashboard" aria-label="رجوع" className="text-text/80">
          <ChevronLeft size={24} strokeWidth={2} />
        </Link>
        <div className="flex items-center gap-2">
          <TrendingUp size={20} className="text-primary" strokeWidth={2.25} />
          <h1 className="text-[17px] font-bold text-text">تحليل المهارات</h1>
        </div>
        <Link href="/add-course" aria-label="إضافة مقرر" className="text-primary">
          <Plus size={22} strokeWidth={2} />
        </Link>
      </header>

      {/* Tabs */}
      <div className="border-b border-black/[0.08] px-5">
        <div className="flex items-center gap-6">
          <button
            onClick={() => setActiveTab("all")}
            className={`py-3 text-[13.5px] font-medium transition-colors ${
              activeTab === "all" ? "relative font-bold text-primary" : "text-muted"
            }`}
          >
            الكل
            {activeTab === "all" && (
              <span className="absolute inset-x-0 -bottom-px h-[2.5px] rounded-t bg-primary" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("confirmed")}
            className={`relative py-3 text-[13.5px] font-medium transition-colors ${
              activeTab === "confirmed" ? "font-bold text-primary" : "text-muted"
            }`}
          >
            المهارات المؤكدة
            {activeTab === "confirmed" && (
              <span className="absolute inset-x-0 -bottom-px h-[2.5px] rounded-t bg-primary" />
            )}
          </button>

          <Link
            href="/recommended"
            className="flex items-center gap-1.5 py-3 text-[13.5px] font-medium text-muted"
          >
            <span>الموصى بها</span>
            {recommendedCount > 0 && (
              <span className="rounded-full bg-purple-light px-1.5 py-0.5 text-[10.5px] font-semibold text-primary">
                {recommendedCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      {status === "loading" && <LoadingSpinner />}
      {status === "error" && <ErrorState onRetry={retry} />}

      {status === "ready" && skills && (
        <>
          {/* "الكل" tab — flat list */}
          {activeTab === "all" && (
            <>
              <section className="px-5 pt-6 pb-3">
                <h2 className="text-[16px] font-bold text-text">
                  جميع مهاراتك{" "}
                  <span className="text-text/70">({flat.length})</span>
                </h2>
              </section>
              {flat.length === 0 ? (
                <EmptyState />
              ) : (
                <section className="space-y-2.5 px-5">
                  {flat.map((s) => (
                    <SkillCard key={`${s.category}-${s.id}`} skill={s} />
                  ))}
                </section>
              )}
            </>
          )}

          {/* "المهارات المؤكدة" tab — grouped */}
          {activeTab === "confirmed" && (
            <>
              {/* Onboarding-selected skills section */}
              {selfSkills.length > 0 && (
                <>
                  <section className="px-5 pt-6 pb-3">
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                        {selfSkills.length} مهارة
                      </span>
                      <h2 className="text-[16px] font-bold text-text">اخترتها في التسجيل</h2>
                    </div>
                    <p className="mt-1 text-right text-[12.5px] text-muted">
                      مهارات أكدت امتلاكها عند إنشاء حسابك
                    </p>
                  </section>
                  <section className="space-y-2.5 px-5">
                    {selfSkills.map((s) => (
                      <SkillCard key={`self-${s.id}`} skill={s} />
                    ))}
                  </section>
                </>
              )}

              {/* Course-based skills section */}
              {courseSkills.length > 0 && (
                <>
                  <section className="px-5 pt-6 pb-3">
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-black/[0.06] px-2.5 py-1 text-[11px] font-semibold text-muted">
                        {courseSkills.length} مهارة
                      </span>
                      <h2 className="text-[16px] font-bold text-text">من مقرراتك الدراسية</h2>
                    </div>
                    <p className="mt-1 text-right text-[12.5px] text-muted">
                      مهارات تلبي متطلبات سوق العمل
                    </p>
                  </section>
                  <section className="space-y-2.5 px-5">
                    {courseSkills.map((s) => (
                      <SkillCard key={`course-${s.category}-${s.id}`} skill={s} />
                    ))}
                  </section>
                </>
              )}

              {flat.length === 0 && <EmptyState />}
            </>
          )}
        </>
      )}

      <BottomNav />
    </div>
  );
}
