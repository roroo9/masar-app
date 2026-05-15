"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

const PUBLIC_PATHS = ["/", "/login", "/onboarding"];

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!PUBLIC_PATHS.includes(pathname) && !isAuthenticated()) {
      router.replace("/login");
    }
  }, [pathname, router]);

  return <>{children}</>;
}
