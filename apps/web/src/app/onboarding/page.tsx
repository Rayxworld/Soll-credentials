"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, ensureCsrfToken, Organization, ApiError } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        await ensureCsrfToken();
        const rows = await apiRequest<Organization[]>("/api/v1/organizations");
        if (!active) return;
        setOrganizations(rows);
        if (rows.length > 0) router.replace("/");
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) router.replace("/login");
        else if (active) setError(err instanceof Error ? err.message : "Could not load organisations.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [router]);

  async function createOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiRequest<Organization>("/api/v1/organizations", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the organisation.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f5ef] px-5 py-10">
      <section className="w-full max-w-xl rounded-[26px] border border-[#e3e7de] bg-[#fbfcf8] p-7 shadow-sm sm:p-9">
        <p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#66836d]">Workspace setup</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-.05em] text-[#18392c]">Create your organisation</h1>
        <p className="mt-3 text-sm leading-6 text-[#78857a]">Set up the organisation that will manage programmes, recipients and credentials in SOLL. Your account will become its owner.</p>

        {loading ? (
          <p className="mt-8 text-sm text-[#78857a]">Checking your account…</p>
        ) : (
          <form onSubmit={createOrganization} className="mt-8 space-y-4">
            <label className="block text-sm font-medium text-[#294334]">
              Organisation name
              <input
                required
                minLength={2}
                maxLength={160}
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[#dce3d8] bg-white px-4 py-3 text-sm outline-none focus:border-[#668b6a]"
                placeholder="e.g. Port Harcourt Tech Academy"
              />
            </label>
            <button disabled={busy || name.trim().length < 2} className="w-full rounded-xl bg-[#173b30] px-5 py-3.5 text-sm font-semibold text-white disabled:opacity-60">
              {busy ? "Creating workspace…" : "Create organisation"}
            </button>
          </form>
        )}
        {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </section>
    </main>
  );
}
