const TOKEN_KEY = "masar_token";
const STUDENT_KEY = "masar_student_id";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStudentId(): number {
  if (typeof window === "undefined") return 0;
  const stored = localStorage.getItem(STUDENT_KEY);
  return stored ? parseInt(stored, 10) : 0;
}

export function setAuth(token: string, studentId: number): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(STUDENT_KEY, String(studentId));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(STUDENT_KEY);
  localStorage.removeItem("masar_profile");
  localStorage.removeItem("masar_plan");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
