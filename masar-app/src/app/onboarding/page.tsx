'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronLeft } from 'lucide-react'
import { register, addExtraSkills, getAllSkillsList, getDashboard, getReadiness, type SkillListItem } from '@/lib/api'
import { setAuth, getStudentId } from '@/lib/auth'

type Profile = {
  name: string
  email: string
  password: string
  university: string
  major: string
  graduationYear: string
  targetRole: string
}

function Logo() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <path d="M4 18 L4 4 L18 4" stroke="#5D3FD3" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const ROLES = ['محلل بيانات', 'مهندس برمجيات', 'مطور ويب', 'عالم بيانات', 'مهندس سحابي', 'مدير منتج']
const YEARS = ['2025', '2026', '2027', '2028', '2029']
const TOTAL_STEPS = 4

function gradYearToYearOfStudy(gradYear: string): number {
  const current = new Date().getFullYear()
  const grad = parseInt(gradYear, 10)
  const yearsLeft = Math.max(0, grad - current)
  return Math.max(1, Math.min(4, 4 - yearsLeft))
}

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [skills, setSkills] = useState<SkillListItem[]>([])
  const [selectedSkillIds, setSelectedSkillIds] = useState<Set<number>>(new Set())
  const [profile, setProfile] = useState<Profile>({
    name: '', email: '', password: '', university: '', major: '', graduationYear: '', targetRole: '',
  })

  // Pre-fetch skills when reaching step 4
  useEffect(() => {
    if (step === 4 && skills.length === 0) {
      getAllSkillsList().then(r => setSkills(r.skills)).catch(() => {})
    }
  }, [step, skills.length])

  function update(field: keyof Profile, value: string) {
    setProfile(prev => ({ ...prev, [field]: value }))
  }

  function toggleSkill(id: number) {
    setSelectedSkillIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function canAdvance() {
    if (step === 1) return profile.name.trim().length > 0 && profile.email.trim().includes('@') && profile.password.length >= 6
    if (step === 2) return profile.university.trim().length > 0 && profile.major.trim().length > 0
    if (step === 3) return profile.graduationYear !== '' && profile.targetRole !== ''
    return true // step 4 is always skippable
  }

  async function handleNext() {
    if (step < TOTAL_STEPS) {
      setStep(step + 1)
      return
    }

    setLoading(true)
    try {
      let studentId: number | null = null
      try {
        const result = await register({
          name: profile.name,
          email: profile.email,
          password: profile.password,
          major: profile.major,
          year_of_study: gradYearToYearOfStudy(profile.graduationYear),
          university: profile.university,
        })
        setAuth(result.token, result.student_id)
        studentId = result.student_id
      } catch {
        // email already registered — fall back to existing session
        studentId = getStudentId()
      }

      // Add skills and fetch dashboard in parallel
      const [, dashboard] = await Promise.all([
        selectedSkillIds.size > 0 && studentId
          ? addExtraSkills(studentId, [...selectedSkillIds]).catch(() => {})
          : Promise.resolve(),
        studentId ? getDashboard(studentId).catch(() => null) : Promise.resolve(null),
      ])

      if (studentId && dashboard) {
        try {
          // Try to find a job matching the selected target role
          const roleKeywords: Record<string, string> = {
            'محلل بيانات': 'analyst',
            'مهندس برمجيات': 'software',
            'مطور ويب': 'web',
            'عالم بيانات': 'scientist',
            'مهندس سحابي': 'cloud',
            'مدير منتج': 'product',
          }
          const keyword = profile.targetRole ? roleKeywords[profile.targetRole] : null
          const matched = keyword
            ? dashboard.jobs.find(j => j.title.toLowerCase().includes(keyword))
            : null
          const jobId = matched?.job_id ?? dashboard.top_scores[0]?.job_id ?? dashboard.jobs[0]?.job_id
          if (jobId != null) {
            getReadiness(studentId, jobId).catch(() => {}) // fire-and-forget
          }
        } catch { /* non-blocking — dashboard will retry */ }
      }

      localStorage.setItem('masar_profile', JSON.stringify(profile))
      setLoading(false)
      router.push('/dashboard')
    } catch {
      localStorage.setItem('masar_profile', JSON.stringify(profile))
      setLoading(false)
      router.push('/dashboard')
    }
  }

  const categoryLabel: Record<string, string> = {
    technical: 'تقنية',
    soft: 'شخصية',
    domain: 'تخصصية',
  }

  const skillsByCategory = skills.reduce<Record<string, SkillListItem[]>>((acc, s) => {
    const cat = s.category ?? 'other'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(s)
    return acc
  }, {})

  return (
    <div className="flex min-h-screen flex-col bg-canvas px-5">
      {/* Header */}
      <header className="flex items-center justify-between pt-5 pb-6">
        {step > 1 ? (
          <button onClick={() => setStep(step - 1)} aria-label="رجوع" className="text-text/80 active:text-primary">
            <ChevronLeft size={24} strokeWidth={2} />
          </button>
        ) : (
          <span className="w-6" aria-hidden />
        )}
        <div className="flex items-center gap-2">
          <span className="text-[18px] font-bold tracking-tight text-text">مسار</span>
          <Logo />
        </div>
        <span className="w-6" aria-hidden />
      </header>

      {/* Progress dots */}
      <div className="mb-8 flex justify-center gap-2">
        {Array.from({ length: TOTAL_STEPS }, (_, i) => i + 1).map(i => (
          <div
            key={i}
            className={`h-2 rounded-full transition-all duration-300 ${
              i === step ? 'w-6 bg-primary' : i < step ? 'w-2 bg-primary/40' : 'w-2 bg-black/10'
            }`}
          />
        ))}
      </div>

      {/* Step content */}
      <div className="flex-1 overflow-y-auto">
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <h1 className="text-[24px] font-bold leading-tight text-text">مرحباً بك في مسار</h1>
              <p className="mt-2 text-[14px] leading-relaxed text-muted">سنساعدك على بناء مسارك المهني وقياس جاهزيتك لسوق العمل</p>
            </div>
            <div>
              <label className="mb-2 block text-[13.5px] font-semibold text-text">الاسم</label>
              <input type="text" placeholder="أدخل اسمك الكريم" value={profile.name}
                onChange={e => update('name', e.target.value)}
                className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div>
              <label className="mb-2 block text-[13.5px] font-semibold text-text">البريد الإلكتروني</label>
              <input type="email" placeholder="example@university.edu.sa" value={profile.email}
                onChange={e => update('email', e.target.value)} dir="ltr"
                className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div>
              <label className="mb-2 block text-[13.5px] font-semibold text-text">كلمة المرور</label>
              <input type="password" placeholder="6 أحرف على الأقل" value={profile.password}
                onChange={e => update('password', e.target.value)} dir="ltr"
                className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-[24px] font-bold leading-tight text-text">معلوماتك الأكاديمية</h1>
              <p className="mt-2 text-[14px] text-muted">نستخدمها لتحليل مهاراتك من مقرراتك الدراسية</p>
            </div>
            <div>
              <label className="mb-2 block text-[13.5px] font-semibold text-text">الجامعة</label>
              <input type="text" placeholder="مثل: جامعة الملك عبدالله" value={profile.university}
                onChange={e => update('university', e.target.value)}
                className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div>
              <label className="mb-2 block text-[13.5px] font-semibold text-text">التخصص</label>
              <input type="text" placeholder="مثل: علوم الحاسب" value={profile.major}
                onChange={e => update('major', e.target.value)}
                className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-[24px] font-bold leading-tight text-text">هدفك المهني</h1>
              <p className="mt-2 text-[14px] text-muted">سنقيس جاهزيتك بناءً على هذا الهدف</p>
            </div>
            <div>
              <label className="mb-3 block text-[13.5px] font-semibold text-text">سنة التخرج</label>
              <div className="grid grid-cols-5 gap-2">
                {YEARS.map(y => (
                  <button key={y} onClick={() => update('graduationYear', y)}
                    className={`rounded-xl py-3 text-[13.5px] font-semibold transition-colors ${
                      profile.graduationYear === y ? 'bg-primary text-white' : 'border border-black/[0.12] bg-white text-text'
                    }`}>{y}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-3 block text-[13.5px] font-semibold text-text">الوظيفة المستهدفة</label>
              <div className="space-y-2">
                {ROLES.map(role => (
                  <button key={role} onClick={() => update('targetRole', role)}
                    className={`w-full rounded-xl px-4 py-3.5 text-right text-[15px] font-semibold transition-colors ${
                      profile.targetRole === role ? 'bg-primary text-white' : 'border border-black/[0.12] bg-white text-text'
                    }`}>{role}</button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-5 pb-4">
            <div>
              <h1 className="text-[24px] font-bold leading-tight text-text">مهاراتك الحالية</h1>
              <p className="mt-2 text-[14px] text-muted">اختر المهارات التي تمتلكها بالفعل — ستُضاف إلى مهاراتك المؤكدة</p>
            </div>

            {selectedSkillIds.size > 0 && (
              <div className="rounded-xl bg-purple-light px-4 py-2.5 text-right text-[13px] font-semibold text-primary">
                تم اختيار {selectedSkillIds.size} مهارة
              </div>
            )}

            {skills.length === 0 ? (
              <div className="flex justify-center py-8">
                <div className="h-6 w-6 animate-spin rounded-full border-[3px] border-purple-light border-t-primary" />
              </div>
            ) : (
              Object.entries(skillsByCategory).map(([cat, catSkills]) => (
                <div key={cat}>
                  <p className="mb-2.5 text-[12.5px] font-semibold text-muted">
                    {categoryLabel[cat] ?? cat}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {catSkills.map(skill => {
                      const selected = selectedSkillIds.has(skill.id)
                      return (
                        <button
                          key={skill.id}
                          onClick={() => toggleSkill(skill.id)}
                          className={`rounded-full px-3.5 py-1.5 text-[13px] font-semibold transition-colors ${
                            selected
                              ? 'bg-primary text-white'
                              : 'border border-black/[0.12] bg-white text-text'
                          }`}
                        >
                          {skill.name}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="sticky bottom-0 bg-canvas pb-8 pt-4">
        {step === 4 && (
          <button
            onClick={() => router.push('/dashboard')}
            className="mb-3 w-full rounded-xl border border-black/[0.12] bg-white py-3.5 text-[14px] font-semibold text-muted"
          >
            تخطي
          </button>
        )}
        <button
          onClick={handleNext}
          disabled={!canAdvance() || loading}
          className="w-full rounded-xl bg-primary py-4 text-[15px] font-bold text-white disabled:opacity-35 active:bg-primary/90"
        >
          {loading ? 'جاري الحفظ...' : step === TOTAL_STEPS ? 'ابدأ رحلتك ←' : 'التالي ←'}
        </button>
      </div>
    </div>
  )
}
