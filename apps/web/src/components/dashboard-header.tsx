"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, clearCsrfToken, ApiError } from "@/lib/api";

export default function DashboardHeader({ title }: { title: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function signOut() {
    setBusy(true);
    setError("");
    try {
      await apiRequest<{ message: string }>("/api/v1/auth/logout", {
        method: "POST",
      });
      clearCsrfToken();
      router.replace("/login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign out. Try again.");
      setBusy(false);
    }
  }

  return (
    <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-[#e3e6dd] pb-5 print:hidden">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[.19em] text-[#879188]"><strong className="font-extrabold text-[#526b5a]">SOLL</strong> Network <span className="px-1 text-[#bdc5ba]">/</span> Workspace</p>
        <h2 className="mt-1.5 text-[22px] font-semibold tracking-[-.045em] text-[#17251f]">{title}</h2>
        {error && <p role="alert" className="mt-2 text-xs text-red-700">{error}</p>}
      </div>
      <div className="flex items-center gap-3">
        <span className="rounded-full border border-[#dfe5d9] bg-[#fbfcf8] px-3 py-2 text-[11px] font-semibold text-[#557061]">TESTNET</span>
        <button
          type="button"
          onClick={signOut}
          disabled={busy}
          className="rounded-full border border-[#dfe5d9] px-3 py-2 text-[11px] font-semibold text-[#557061] transition hover:bg-white disabled:opacity-60"
        >
          {busy ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </header>
  );
}
