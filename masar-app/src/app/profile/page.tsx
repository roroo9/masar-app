'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import {
  CheckCircle2,
  Star,
  Zap,
  Home,
  BookOpen,
  UserRound,
  Lightbulb,
  Calendar,
  Pencil,
  LogOut,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import {
  getStudent,
  getDashboard,
  getReadiness,
  getStudentId,
  type Student,
  type DashboardResponse,
  type ReadinessResponse,
} from '@/lib/api'
import { LoadingSpinner } from '@/lib/states'

type LocalProfile = {
  name: string
  university: string
  major: string
  graduationYear: string
  targetRole: string
}

const DEFAULT_LOCAL: LocalProfile = {
  name: 'خالد',
  university: 'جامعة الملك عبدالله',
  major: 'علوم الحاسب',
  graduationYear: '2026',
  targetRole: 'محلل بيانات',
}

function BottomNav() {
  const items = [
    { href: '/dashboard', label: 'الرئيسية', icon: Home },
    { href: '/skills', label: 'المهارات', icon: BookOpen },
    { href: '/recommended', label: 'الفرص', icon: Lightbulb },
    { href: '/plan', label: 'الخطة', icon: Calendar },
    { href: '/profile', label: 'ملفي', icon: UserRound, active: true },
  ]
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 mx-auto w-full max-w-[390px] border-t border-black/[0.06] bg-white">
      <ul className="grid grid-cols-5 px-2 pb-3 pt-2">
        {items.map((it) => {
          const Icon = it.icon
          return (
            <li key={it.label}>
              <Link
                href={it.href as never}
                className={`flex flex-col items-center gap-1 py-1.5 ${
                  it.active ? 'text-primary' : 'text-muted'
                }`}
              >
                <Icon
                  size={22}
                  strokeWidth={it.active ? 2.25 : 1.75}
                  fill={it.active ? 'currentColor' : 'none'}
                  fillOpacity={it.active ? 0.08 : 0}
                />
                <span className="text-[11px] font-medium">{it.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

export default function ProfilePage() {
  const router = useRouter()
  const [local, setLocal] = useState<LocalProfile>(DEFAULT_LOCAL)
  const [student, setStudent] = useState<Student | null>(null)
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    const stored = localStorage.getItem('masar_profile')
    if (stored) {
      try { setLocal(JSON.parse(stored)) } catch { /* keep default */ }
    }

    const studentId = getStudentId()
    try {
      const [s, d] = await Promise.all([
        getStudent(studentId),
        getDashboard(studentId),
      ])
      setStudent(s)
      setDashboard(d)

      const topJobId = d.top_scores[0]?.job_id ?? d.jobs[0]?.job_id
      if (topJobId != null) {
        try {
          const r = await getReadiness(studentId, topJobId)
          setReadiness(r)
        } catch { /* no readiness yet */ }
      }
    } catch { /* API unavailable, show localStorage data */ }
    setLoading(false)
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const displayName = student?.name ?? local.name
  const displayUniversity = student?.university ?? local.university
  const displayMajor = student?.major ?? local.major
  const initials = displayName.trim().charAt(0) || 'م'
  const totalSkills = dashboard?.total_skills ?? 0
  const recommendedCount = readiness?.missing_skills.length ?? 0
  const readinessScore = readiness ? Math.round(readiness.score) : null

  return (
    <div className="min-h-screen bg-canvas pb-24">
      {/* Hero */}
      <div className="bg-primary px-5 pb-8 pt-12 text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white/20">
            <span className="text-[32px] font-bold text-white">{initials}</span>
          </div>
          <div className="text-center">
            <h1 className="text-[22px] font-bold">{displayName}</h1>
            <p className="mt-1 text-[13px] text-white/80">{displayMajor} · {displayUniversity}</p>
          </div>
          <span className="mt-1 rounded-full bg-white/20 px-3.5 py-1.5 text-[12.5px] font-semibold">
            {local.targetRole}
          </span>
        </div>
      </div>

      {/* Info card */}
      <section className="px-5 -mt-4">
        <div className="rounded-2xl border border-black/[0.06] bg-white p-4 shadow-sm">
          <div className="grid grid-cols-2 divide-x divide-x-reverse divide-black/[0.06]">
            <div className="pl-4 text-right">
              <p className="text-[11.5px] text-muted">التخصص</p>
              <p className="mt-0.5 text-[14px] font-semibold text-text">{displayMajor}</p>
            </div>
            <div className="pr-4 text-right">
              <p className="text-[11.5px] text-muted">سنة التخرج</p>
              <p className="mt-0.5 text-[14px] font-semibold text-text">{local.graduationYear}</p>
            </div>
          </div>
        </div>
      </section>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Stats */}
          <section className="mt-5 px-5">
            <h2 className="mb-3 text-[15px] font-bold text-text">إنجازاتك</h2>
            <div className="grid grid-cols-3 gap-2.5">
              <div className="rounded-xl border border-black/[0.06] bg-white p-3 text-center">
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center">
                  <CheckCircle2 size={20} className="text-emerald-600" strokeWidth={2} />
                </div>
                <p className="text-[11px] leading-tight text-muted">المهارات المؤكدة</p>
                <p className="mt-1 text-[22px] font-bold text-text">{totalSkills || '—'}</p>
              </div>
              <div className="rounded-xl border border-black/[0.06] bg-white p-3 text-center">
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center">
                  <Star size={20} className="text-primary" strokeWidth={2} fill="currentColor" />
                </div>
                <p className="text-[11px] leading-tight text-muted">الموصى بها</p>
                <p className="mt-1 text-[22px] font-bold text-text">{recommendedCount || '—'}</p>
              </div>
              <div className="rounded-xl border border-black/[0.06] bg-white p-3 text-center">
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center">
                  <Zap size={20} className="text-primary" strokeWidth={2} fill="currentColor" />
                </div>
                <p className="text-[11px] leading-tight text-muted">المهارات المطابقة</p>
                <p className="mt-1 text-[22px] font-bold text-text">{readiness?.matched_skills.length ?? '—'}</p>
              </div>
            </div>
          </section>

          {/* Readiness */}
          {readinessScore !== null && (
            <section className="mt-4 px-5">
              <div className="rounded-xl bg-purple-light p-4">
                <div className="flex items-center justify-between">
                  <span className="text-[22px] font-bold text-primary">{readinessScore}%</span>
                  <p className="text-right text-[14px] font-semibold text-text">
                    جاهزيتك لوظيفة {readiness?.job_title ?? local.targetRole}
                  </p>
                </div>
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${readinessScore}%` }} />
                </div>
              </div>
            </section>
          )}
        </>
      )}

      {/* Edit profile */}
      <section className="mt-5 px-5 space-y-2.5">
        <Link
          href="/onboarding"
          className="flex w-full items-center justify-between rounded-xl border border-black/[0.08] bg-white px-4 py-3.5"
        >
          <Pencil size={18} className="text-primary" strokeWidth={2} />
          <span className="text-[14.5px] font-semibold text-text">تعديل الملف الشخصي</span>
        </Link>
        <button
          onClick={() => {
            localStorage.removeItem('masar_profile')
            localStorage.removeItem('masar_student_id')
            localStorage.removeItem('masar_plan')
            router.push('/onboarding')
          }}
          className="flex w-full items-center justify-between rounded-xl border border-red-100 bg-white px-4 py-3.5"
        >
          <LogOut size={18} className="text-red-400" strokeWidth={2} />
          <span className="text-[14.5px] font-semibold text-red-400">تسجيل خروج</span>
        </button>
      </section>

      <BottomNav />
    </div>
  )
}
