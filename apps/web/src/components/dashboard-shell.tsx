"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/sidebar";
import {
  apiRequest,
  clearCsrfToken,
  ensureCsrfToken,
  Organization,
  AuthenticatedUser,
  ApiError,
} from "@/lib/api";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    async function protectWorkspace() {
      try {
        await apiRequest<AuthenticatedUser>("/api/v1/auth/me");
        await ensureCsrfToken();
        const organizations = await apiRequest<Organization[]>("/api/v1/organizations");
        if (!active) return;
        if (organizations.length === 0) {
          router.replace("/onboarding");
          return;
        }
        setReady(true);
      } catch (error) {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          clearCsrfToken();
          router.replace("/login");
        } else {
          setFailed(true);
        }
      }
    }
    void protectWorkspace();
    return () => { active = false; };
  }, [router]);

  if (!ready) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f5f5ef] px-5">
        <div className="max-w-sm text-center">
          <p className="text-sm text-[#78857a]">
            {failed ? "SOLL could not reach the API. Check your connection and reload." : "Securing your SOLL workspace…"}
          </p>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f5ef] print:min-h-0 print:bg-white md:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 px-4 py-5 sm:px-7 lg:px-10 lg:py-8 print:w-full print:p-0">
        <div className="mx-auto w-full max-w-[1440px] print:max-w-none">{children}</div>
      </main>
    </div>
  );
}
