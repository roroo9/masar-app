'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ChevronLeft, Search, CheckCircle2 } from 'lucide-react'
import { getCourses, addStudentCourses, getStudentId, type Course } from '@/lib/api'
import { ErrorState, LoadingSpinner } from '@/lib/states'

export default function CoursesPage() {
  const router = useRouter()
  const [courses, setCourses] = useState<Course[]>([])
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading')
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const load = useCallback(async () => {
    try {
      const res = await getCourses()
      setCourses(res.courses)
      setStatus('ready')
    } catch {
      setStatus('error')
    }
  }, [])

  useEffect(() => { load() }, [load])

  function toggle(code: string) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(code) ? next.delete(code) : next.add(code)
      return next
    })
  }

  async function handleSave() {
    if (selected.size === 0) return
    setSaving(true)
    try {
      await addStudentCourses(getStudentId(), [...selected])
      setSaved(true)
      setTimeout(() => router.push('/skills'), 1200)
    } catch {
      setSaving(false)
    }
  }

  const filtered = courses.filter(c =>
    query.trim() === '' ||
    c.title.toLowerCase().includes(query.toLowerCase()) ||
    c.course_code.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-canvas pb-32">
      {/* Header */}
      <header className="flex items-center justify-between px-5 pt-5 pb-4">
        <Link href="/skills" aria-label="رجوع" className="text-text/80">
          <ChevronLeft size={24} strokeWidth={2} />
        </Link>
        <h1 className="text-[17px] font-bold text-text">أضف مقرراتك</h1>
        <span className="w-6" aria-hidden />
      </header>

      {/* Subtitle */}
      <p className="px-5 pb-4 text-right text-[13px] text-muted">
        اختر المقررات التي أتممتها — ستُحدَّث مهاراتك المؤكدة تلقائياً
      </p>

      {/* Search */}
      <div className="px-5 pb-4">
        <div className="flex items-center gap-2.5 rounded-xl border border-black/[0.10] bg-white px-3.5 py-3">
          <Search size={17} className="text-muted" strokeWidth={1.75} />
          <input
            type="text"
            placeholder="ابحث عن مقرر..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-right text-[14px] text-text placeholder:text-muted/60 outline-none"
          />
        </div>
      </div>

      {selected.size > 0 && (
        <div className="mx-5 mb-4 rounded-xl bg-purple-light px-4 py-2.5 text-right text-[13px] font-semibold text-primary">
          تم اختيار {selected.size} مقرر
        </div>
      )}

      {status === 'loading' && <LoadingSpinner />}
      {status === 'error' && <ErrorState onRetry={load} />}

      {status === 'ready' && (
        <section className="space-y-2 px-5">
          {filtered.length === 0 && (
            <p className="py-6 text-center text-[13px] text-muted">لا توجد نتائج</p>
          )}
          {filtered.map(course => {
            const isSelected = selected.has(course.course_code)
            return (
              <button
                key={course.id}
                onClick={() => toggle(course.course_code)}
                className={`w-full rounded-xl border p-4 text-right transition-colors ${
                  isSelected
                    ? 'border-primary bg-purple-subtle'
                    : 'border-black/[0.06] bg-white'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                    isSelected ? 'border-primary bg-primary' : 'border-black/20'
                  }`}>
                    {isSelected && <CheckCircle2 size={12} className="text-white" strokeWidth={3} />}
                  </div>
                  <div className="flex-1">
                    <p className="text-[14.5px] font-bold text-text leading-snug">{course.title}</p>
                    <div className="mt-1 flex items-center justify-end gap-2">
                      <span className="text-[11.5px] text-muted">{course.course_code}</span>
                      {course.skill_count > 0 && (
                        <span className="rounded-full bg-purple-light px-2 py-0.5 text-[10.5px] font-semibold text-primary">
                          {course.skill_count} مهارة
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </section>
      )}

      {/* Save bar */}
      {status === 'ready' && (
        <div className="fixed inset-x-0 bottom-0 mx-auto w-full max-w-[390px] border-t border-black/[0.06] bg-canvas px-5 pb-8 pt-4">
          <button
            onClick={handleSave}
            disabled={selected.size === 0 || saving || saved}
            className="w-full rounded-xl bg-primary py-4 text-[15px] font-bold text-white disabled:opacity-40 active:bg-primary/90"
          >
            {saved ? 'تم الحفظ ✓' : saving ? 'جاري الحفظ...' : `حفظ ${selected.size > 0 ? `(${selected.size})` : ''}`}
          </button>
        </div>
      )}
    </div>
  )
}
