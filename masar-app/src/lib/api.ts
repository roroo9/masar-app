const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export { getStudentId } from "@/lib/auth";

export type StudentSkill = {
  id: number;
  name: string;
  confidence: number;
  source?: string;
};

export type StudentSkillsResponse = {
  total_skills: number;
  technical: StudentSkill[];
  soft: StudentSkill[];
  domain: StudentSkill[];
};

export type Student = {
  id: number;
  name: string;
  email: string;
  major: string;
  year_of_study: number;
  university: string;
};

export type DashboardJob = {
  job_id: number;
  title: string;
  company: string;
  location: string | null;
  readiness_score: number | null;
};

export type TopScore = {
  job_id: number;
  score: number;
  title: string;
  company: string;
};

export type DashboardResponse = {
  student: Student;
  total_skills: number;
  top_scores: TopScore[];
  jobs: DashboardJob[];
};

export type MatchedSkill = {
  skill: string;
  matched_with: string;
  similarity: number;
  source: string;
  weight: number;
};

export type PartialSkill = {
  skill: string;
  closest_match: string | null;
  similarity: number;
  weight: number;
  gap_description: string;
};

export type MissingSkill = {
  skill: string;
  category: string;
  weight: number;
  is_required: boolean;
  priority: string;
};

export type ImprovementArea = {
  skill: string;
  why_it_matters: string;
  how_to_learn: string;
  time_estimate: string;
};

export type Explanation = {
  summary: string;
  strengths: string[];
  improvement_areas: ImprovementArea[];
  next_steps: string[];
  motivational_close: string;
};

export type ReadinessResponse = {
  score: number;
  job_title?: string;
  matched_skills: MatchedSkill[];
  missing_skills: MissingSkill[];
  partial_skills: PartialSkill[];
  breakdown?: {
    achieved_weight: number;
    total_weight: number;
    percentage: number;
  };
  explanation: Explanation | Record<string, never>;
  cached?: boolean;
};

export type TopDemandedSkill = {
  name: string;
  category: string;
  job_demand: number;
};

export type TopDemandedResponse = {
  top_skills: TopDemandedSkill[];
};

export type JobsResponse = {
  jobs: { id: number; title: string; company: string; location: string | null }[];
  total: number;
};

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("masar_token") : null;
  return token
    ? { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...extra }
    : { "Content-Type": "application/json", ...extra };
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export type StudentCreateInput = {
  name: string;
  email: string;
  major: string;
  year_of_study: number;
  university: string;
};

export function createStudent(
  data: StudentCreateInput,
): Promise<{ id: number; message: string }> {
  return postJSON("/api/students", data);
}

export function getStudent(studentId: number): Promise<Student> {
  return getJSON<Student>(`/api/students/${studentId}`);
}

export function getDashboard(studentId: number): Promise<DashboardResponse> {
  return getJSON<DashboardResponse>(`/api/students/${studentId}/dashboard`);
}

export function getStudentSkills(
  studentId: number,
): Promise<StudentSkillsResponse> {
  return getJSON<StudentSkillsResponse>(`/api/students/${studentId}/skills`);
}

export function getReadiness(
  studentId: number,
  jobId: number,
  force?: boolean,
  explanation?: boolean,
): Promise<ReadinessResponse> {
  const params = new URLSearchParams();
  if (force) params.set("force", "true");
  if (explanation) params.set("explanation", "true");
  const qs = params.toString() ? `?${params.toString()}` : "";
  return getJSON<ReadinessResponse>(
    `/api/students/${studentId}/readiness/${jobId}${qs}`,
  );
}

export function getTopDemandedSkills(): Promise<TopDemandedResponse> {
  return getJSON<TopDemandedResponse>(`/api/skills/top-demanded`);
}

export function getAllJobs(): Promise<JobsResponse> {
  return getJSON<JobsResponse>(`/api/jobs/`);
}

export type SkillListItem = {
  id: number;
  name: string;
  category: string;
};

export type SkillsListResponse = {
  skills: SkillListItem[];
  total: number;
};

export type Course = {
  id: number;
  course_code: string;
  title: string;
  department: string | null;
  skill_count: number;
};

export type CoursesResponse = {
  courses: Course[];
  total: number;
};

export function getAllSkillsList(): Promise<SkillsListResponse> {
  return getJSON<SkillsListResponse>(`/api/skills/`);
}

export function getCourses(): Promise<CoursesResponse> {
  return getJSON<CoursesResponse>(`/api/courses/`);
}

export function addStudentCourses(
  studentId: number,
  courseCodes: string[],
): Promise<{ added_courses: string[]; not_found: string[]; count: number }> {
  return postJSON(`/api/students/${studentId}/courses`, {
    course_codes: courseCodes,
  });
}

export function addExtraSkills(
  studentId: number,
  skillIds: number[],
): Promise<{ added: number; skill_ids: number[] }> {
  return postJSON(`/api/students/${studentId}/extra-skills`, {
    skill_ids: skillIds,
    proficiency: 4,
    source: "self_reported",
  });
}

export type Project = {
  id: number;
  title: string;
  company: string;
  description: string;
  difficulty: string;
  required_skills: string[];
  estimated_hours: number;
  relevance_score: number;
  skills_you_will_learn: string[];
};

export type ProjectsResponse = {
  projects: Project[];
};

export function getStudentProjects(
  studentId: number,
  jobId?: number,
): Promise<ProjectsResponse> {
  const qs = jobId != null ? `?job_id=${jobId}` : "";
  return getJSON<ProjectsResponse>(`/api/students/${studentId}/projects${qs}`);
}

export type ExtractedSkill = {
  id: number;
  name: string;
  category: string;
};

export type ExtractFromDescriptionResponse = {
  skills: ExtractedSkill[];
};

export type LearningResource = {
  title: string;
  platform: string;
  url: string;
  type: "video" | "course" | "docs" | "practice";
  language: "ar" | "en";
  free: boolean;
  duration: string;
};

export type SkillResourcesResponse = {
  skill: string;
  resources: LearningResource[];
  source: "curated" | "ai";
};

export function confirmSkill(
  studentId: number,
  skillName: string,
): Promise<{ success: boolean; skill_id: number }> {
  return postJSON(`/api/students/${studentId}/confirm-skill`, {
    skill_name: skillName,
  });
}

export function getSkillResources(skill: string): Promise<SkillResourcesResponse> {
  return getJSON<SkillResourcesResponse>(
    `/api/skills/resources?skill=${encodeURIComponent(skill)}`
  );
}

export function extractFromDescription(
  studentId: number,
  courseName: string,
  description: string,
): Promise<ExtractFromDescriptionResponse> {
  return postJSON(`/api/students/${studentId}/extract-from-description`, {
    course_name: courseName,
    description,
  });
}

export function addExtractedSkills(
  studentId: number,
  skillIds: number[],
): Promise<{ added_count: number }> {
  return postJSON(`/api/students/${studentId}/add-extracted-skills`, { skill_ids: skillIds });
}

export async function extractFromPDF(
  studentId: number,
  file: File,
): Promise<ExtractFromDescriptionResponse> {
  const form = new FormData();
  form.append("file", file);
  const token = typeof window !== "undefined" ? localStorage.getItem("masar_token") : null;
  const res = await fetch(`${API_URL}/api/students/${studentId}/extract-from-pdf`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return (await res.json()) as ExtractFromDescriptionResponse;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export type AuthResponse = {
  token: string;
  student_id: number;
};

export type RegisterInput = {
  name: string;
  email: string;
  password: string;
  major: string;
  year_of_study: number;
  university: string;
};

export function register(data: RegisterInput): Promise<AuthResponse> {
  return postJSON("/api/auth/register", data);
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return postJSON("/api/auth/login", { email, password });
}
