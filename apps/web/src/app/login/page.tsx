"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, saveCsrfToken, ApiError } from "@/lib/api";

type AuthResponse = {
  user: { id: string; email: string };
  csrf_token: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function requestCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await apiRequest<{ message: string }>("/api/v1/auth/request-code", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setStep("code");
      setNotice(result.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not request a sign-in code.");
    } finally {
      setBusy(false);
    }
  }

  async function verifyCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await apiRequest<AuthResponse>("/api/v1/auth/verify-code", {
        method: "POST",
        body: JSON.stringify({ email, code }),
      });
      saveCsrfToken(result.csrf_token);
      router.replace("/onboarding");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not verify that code.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f5ef] px-5 py-10">
      <section className="w-full max-w-md rounded-[26px] border border-[#e3e7de] bg-[#fbfcf8] p-7 shadow-sm sm:p-9">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-[13px] bg-[#173b30] text-lg font-black text-[#c9ef78]">S.</span>
          <div>
            <p className="text-lg font-extrabold tracking-tight text-[#173b30]">SOLL</p>
            <p className="text-[10px] font-semibold uppercase tracking-[.18em] text-[#879188]">Credential infrastructure</p>
          </div>
        </div>
        <p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#66836d]">Secure workspace access</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-.05em] text-[#18392c]">
          {step === "email" ? "Sign in or create an account" : "Check your email"}
        </h1>
        <p className="mt-3 text-sm leading-6 text-[#78857a]">
          {step === "email"
            ? "We'll send you a one-time verification code. No password required."
            : `Enter the verification code sent to ${email}.`}
        </p>

        {step === "email" ? (
          <form onSubmit={requestCode} className="mt-7 space-y-4">
            <label className="block text-sm font-medium text-[#294334]">
              Email address
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[#dce3d8] bg-white px-4 py-3 text-sm outline-none focus:border-[#668b6a]"
                placeholder="you@organisation.com"
              />
            </label>
            <button disabled={busy} className="w-full rounded-xl bg-[#173b30] px-5 py-3.5 text-sm font-semibold text-white disabled:opacity-60">
              {busy ? "Sending code…" : "Continue with email"}
            </button>
          </form>
        ) : (
          <form onSubmit={verifyCode} className="mt-7 space-y-4">
            <label className="block text-sm font-medium text-[#294334]">
              Six-digit code
              <input
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                required
                autoComplete="one-time-code"
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                className="mt-2 w-full rounded-xl border border-[#dce3d8] bg-white px-4 py-3 text-center font-mono text-xl tracking-[.35em] outline-none focus:border-[#668b6a]"
                placeholder="000000"
              />
            </label>
            <button disabled={busy || code.length !== 6} className="w-full rounded-xl bg-[#173b30] px-5 py-3.5 text-sm font-semibold text-white disabled:opacity-60">
              {busy ? "Verifying…" : "Verify and sign in"}
            </button>
            <button type="button" onClick={() => { setStep("email"); setCode(""); setError(""); setNotice(""); }} className="w-full py-2 text-sm font-medium text-[#557061]">
              Use a different email
            </button>
          </form>
        )}

        {notice && <p role="status" className="mt-4 rounded-xl bg-[#edf4e8] p-3 text-sm text-[#315542]">{notice}</p>}
        {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <p className="mt-8 text-xs leading-5 text-[#9aa39a]">By continuing, you confirm that you are authorised to use this email address.</p>
      </section>
    </main>
  );
}
