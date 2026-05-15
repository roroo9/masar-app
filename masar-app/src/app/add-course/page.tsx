"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, BookOpen, CheckCircle, FileText, AlignLeft, Upload } from "lucide-react";
import {
  getStudentId,
  extractFromDescription,
  extractFromPDF,
  type ExtractedSkill,
} from "@/lib/api";

type Mode = "text" | "pdf";
type Status = "idle" | "loading" | "done" | "error";

const categoryLabel: Record<string, string> = {
  technical: "تقنية",
  soft: "شخصية",
  domain: "تخصصية",
};

export default function AddCoursePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [mode, setMode] = useState<Mode>("text");
  const [courseName, setCourseName] = useState("");
  const [description, setDescription] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [extractedSkills, setExtractedSkills] = useState<ExtractedSkill[]>([]);
  const [errorMsg, setErrorMsg] = useState("");

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setPdfFile(f);
  }

  function canSubmit() {
    if (status === "loading") return false;
    if (mode === "text") return description.trim().length > 0;
    return pdfFile !== null;
  }

  async function handleSubmit() {
    setStatus("loading");
    setErrorMsg("");
    try {
      const sid = getStudentId();
      const result =
        mode === "pdf" && pdfFile
          ? await extractFromPDF(sid, pdfFile)
          : await extractFromDescription(sid, courseName, description);
      setExtractedSkills(result.skills);
      setStatus("done");
    } catch (e) {
      setStatus("error");
      setErrorMsg(
        e instanceof Error ? e.message : "حدث خطأ أثناء التحليل. حاول مرة أخرى."
      );
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-canvas px-5">
      <header className="flex items-center justify-between pt-5 pb-6">
        <button
          onClick={() => router.back()}
          aria-label="رجوع"
          className="text-text/80 active:text-primary"
        >
          <ChevronLeft size={24} strokeWidth={2} />
        </button>
        <div className="flex items-center gap-2">
          <span className="text-[17px] font-bold text-text">إضافة مقرر</span>
          <BookOpen size={20} className="text-primary" strokeWidth={2.25} />
        </div>
        <span className="w-6" aria-hidden />
      </header>

      {status !== "done" ? (
        <div className="flex-1 space-y-5">
          <p className="text-right text-[14px] leading-relaxed text-muted">
            أدخل توصيف المقرر أو ارفع ملف PDF وسنستخرج منه المهارات تلقائياً
          </p>

          {/* Mode toggle */}
          <div className="flex rounded-xl border border-black/[0.10] bg-white p-1">
            <button
              onClick={() => setMode("text")}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-[13.5px] font-semibold transition-colors ${
                mode === "text" ? "bg-primary text-white" : "text-muted"
              }`}
            >
              <AlignLeft size={15} strokeWidth={2} />
              نص
            </button>
            <button
              onClick={() => setMode("pdf")}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-[13.5px] font-semibold transition-colors ${
                mode === "pdf" ? "bg-primary text-white" : "text-muted"
              }`}
            >
              <FileText size={15} strokeWidth={2} />
              PDF
            </button>
          </div>

          {mode === "text" ? (
            <>
              <div>
                <label className="mb-2 block text-[13.5px] font-semibold text-text">
                  اسم المقرر (اختياري)
                </label>
                <input
                  type="text"
                  placeholder="مثال: قواعد البيانات المتقدمة"
                  value={courseName}
                  onChange={(e) => setCourseName(e.target.value)}
                  disabled={status === "loading"}
                  className="w-full rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="mb-2 block text-[13.5px] font-semibold text-text">
                  توصيف المقرر
                </label>
                <textarea
                  rows={8}
                  placeholder="الصق هنا توصيف المقرر أو مخرجات التعلم..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={status === "loading"}
                  className="w-full resize-none rounded-xl border border-black/[0.12] bg-white px-4 py-3.5 text-right text-[15px] text-text placeholder:text-muted/60 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="mb-2 block text-[13.5px] font-semibold text-text">
                ملف توصيف المقرر (PDF)
              </label>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={status === "loading"}
                className={`flex w-full flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed py-10 transition-colors disabled:opacity-50 ${
                  pdfFile
                    ? "border-primary/40 bg-purple-subtle"
                    : "border-black/[0.12] bg-white active:border-primary/40"
                }`}
              >
                {pdfFile ? (
                  <>
                    <FileText size={32} className="text-primary" strokeWidth={1.5} />
                    <span className="text-[14px] font-semibold text-primary">
                      {pdfFile.name}
                    </span>
                    <span className="text-[12px] text-muted">
                      {(pdfFile.size / 1024).toFixed(0)} KB · اضغط لتغيير الملف
                    </span>
                  </>
                ) : (
                  <>
                    <Upload size={32} className="text-muted" strokeWidth={1.5} />
                    <span className="text-[14px] font-semibold text-text">
                      اضغط لاختيار ملف PDF
                    </span>
                    <span className="text-[12px] text-muted">الحد الأقصى 10 MB</span>
                  </>
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          )}

          {status === "error" && (
            <p className="text-right text-[13px] text-red-500">{errorMsg}</p>
          )}
        </div>
      ) : (
        <div className="flex-1">
          <div className="mb-6 flex flex-col items-center gap-3 pt-4">
            <CheckCircle size={52} className="text-primary" strokeWidth={1.5} />
            <p className="text-center text-[17px] font-bold text-text">
              {extractedSkills.length > 0
                ? `تم استخراج ${extractedSkills.length} مهارة وإضافتها`
                : "لم يتم التعرف على مهارات واضحة"}
            </p>
            {extractedSkills.length > 0 && (
              <p className="text-center text-[13px] text-muted">
                ستجدها الآن في تبويب المهارات المؤكدة
              </p>
            )}
          </div>

          <div className="space-y-2.5">
            {extractedSkills.map((skill) => (
              <div
                key={skill.id}
                className="flex items-center justify-between rounded-xl border border-primary/20 bg-purple-subtle px-4 py-3"
              >
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10.5px] font-semibold text-primary">
                  {categoryLabel[skill.category] ?? skill.category}
                </span>
                <span className="text-[15px] font-semibold text-text">
                  {skill.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="sticky bottom-0 bg-canvas pb-8 pt-4">
        {status === "done" ? (
          <button
            onClick={() => router.push("/skills")}
            className="w-full rounded-xl bg-primary py-4 text-[15px] font-bold text-white active:bg-primary/90"
          >
            عرض مهاراتي ←
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!canSubmit()}
            className="w-full rounded-xl bg-primary py-4 text-[15px] font-bold text-white disabled:opacity-35 active:bg-primary/90"
          >
            {status === "loading" ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                جاري تحليل المقرر...
              </span>
            ) : (
              "استخراج المهارات ←"
            )}
          </button>
        )}
      </div>
    </div>
  );
}
