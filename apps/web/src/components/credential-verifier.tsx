"use client";

import { useState } from "react";
import type { FormEvent } from "react";

type CredentialStatus = {
  credential_id: string;
  organization_id: string;
  commitment: string;
  issuer: string;
  issued_at: number;
  revoked: boolean;
  network: string;
};

type LookupState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "found"; credential: CredentialStatus }
  | { kind: "missing" }
  | { kind: "unavailable"; message: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

function extractCredentialId(value: string): string {
  const input = value.trim();
  if (!input) return "";

  // Accept either a raw 32-byte hex ID or a verification URL / QR payload.
  try {
    const parsed = new URL(input);
    return (
      parsed.searchParams.get("credential_id") ??
      parsed.searchParams.get("id") ??
      parsed.pathname.split("/").filter(Boolean).at(-1) ??
      ""
    );
  } catch {
    return input;
  }
}

function shortAddress(value: string): string {
  if (value.length <= 18) return value;
  return `${value.slice(0, 9)}…${value.slice(-7)}`;
}

export default function CredentialVerifier() {
  const [value, setValue] = useState("");
  const [state, setState] = useState<LookupState>({ kind: "idle" });

  async function verify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const credentialId = extractCredentialId(value);

    if (!/^[0-9a-fA-F]{64}$/.test(credentialId)) {
      setState({
        kind: "unavailable",
        message: "Enter a valid 64-character credential ID or a SOLL verification link.",
      });
      return;
    }

    if (!API_BASE) {
      setState({
        kind: "unavailable",
        message: "The verification API is not connected to this website yet.",
      });
      return;
    }

    setState({ kind: "loading" });

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/public/credentials/${credentialId.toLowerCase()}`,
        { method: "GET", cache: "no-store", headers: { Accept: "application/json" } },
      );

      if (response.status === 404) {
        setState({ kind: "missing" });
        return;
      }

      if (response.status === 503) {
        setState({
          kind: "unavailable",
          message: "On-chain verification is not configured on the API yet.",
        });
        return;
      }

      if (!response.ok) {
        setState({
          kind: "unavailable",
          message: "The verification service could not complete this check. Try again later.",
        });
        return;
      }

      const credential = (await response.json()) as CredentialStatus;
      if (
        credential.credential_id !== credentialId.toLowerCase() ||
        !/^[0-9a-f]{64}$/.test(credential.commitment) ||
        !/^[0-9a-f]{64}$/.test(credential.organization_id) ||
        typeof credential.revoked !== "boolean" ||
        !Number.isFinite(credential.issued_at)
      ) {
        setState({
          kind: "unavailable",
          message: "The verification service returned an unexpected response.",
        });
        return;
      }

      setState({ kind: "found", credential });
    } catch {
      setState({
        kind: "unavailable",
        message: "Unable to reach the verification API. Check your connection and try again.",
      });
    }
  }

  const result = state.kind === "found" ? state.credential : null;

  return (
    <div className="mx-auto w-full max-w-3xl">
      <div className="rounded-[26px] border border-[#e2e8de] bg-[#fbfcf8] p-5 shadow-[0_24px_80px_rgba(30,57,39,.06)] sm:p-8">
        <div className="mb-7">
          <p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#668267]">Independent credential check</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-.06em] text-[#193b2e] sm:text-4xl">Verify a credential.</h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-[#728076]">
            Check the credential&apos;s on-chain record on the Stellar network. SOLL checks its proof and revocation status without exposing private recipient information.
          </p>
        </div>

        <form onSubmit={verify} className="space-y-3">
          <label htmlFor="credential-id" className="block text-xs font-semibold text-[#435b49]">
            Credential ID or verification link
          </label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              id="credential-id"
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Paste a 64-character credential ID"
              autoComplete="off"
              spellCheck={false}
              className="min-w-0 flex-1 rounded-xl border border-[#dce4d9] bg-white px-4 py-3.5 font-mono text-xs text-[#20392d] outline-none transition placeholder:font-sans placeholder:text-[#a0aaa0] focus:border-[#70936d] focus:ring-4 focus:ring-[#dcebd4]/70"
            />
            <button
              type="submit"
              disabled={state.kind === "loading"}
              className="rounded-xl bg-[#173b30] px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-[#285742] disabled:cursor-wait disabled:opacity-60"
            >
              {state.kind === "loading" ? "Checking…" : "Verify credential"}
            </button>
          </div>
        </form>

        {state.kind === "loading" && (
          <div role="status" className="mt-6 rounded-xl border border-[#e5eadd] bg-[#f4f7ef] p-4 text-sm text-[#5f755f]">
            Querying the credential registry…
          </div>
        )}

        {state.kind === "missing" && (
          <div role="status" className="mt-6 rounded-xl border border-[#eadfca] bg-[#fbf7ed] p-5">
            <p className="font-semibold text-[#72552d]">Credential not found</p>
            <p className="mt-1 text-sm leading-6 text-[#8a7658]">No matching credential record was found on the configured network. Check the ID and try again.</p>
          </div>
        )}

        {state.kind === "unavailable" && (
          <div role="alert" className="mt-6 rounded-xl border border-[#eadfca] bg-[#fbf7ed] p-5">
            <p className="font-semibold text-[#72552d]">Verification unavailable</p>
            <p className="mt-1 text-sm leading-6 text-[#8a7658]">{state.message}</p>
          </div>
        )}

        {result && (
          <section aria-live="polite" className="mt-7 overflow-hidden rounded-2xl border border-[#dfe7dc]">
            <div className={`flex flex-wrap items-center justify-between gap-3 px-5 py-4 ${result.revoked ? "bg-[#fbf1eb]" : "bg-[#edf4e8]"}`}>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#72806f]">Registry result</p>
                <h2 className={`mt-1 text-xl font-semibold tracking-[-.04em] ${result.revoked ? "text-[#914b35]" : "text-[#28553a]"}`}>
                  {result.revoked ? "Credential revoked" : "Credential recorded"}
                </h2>
              </div>
              <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider ${result.revoked ? "bg-[#f3ded5] text-[#914b35]" : "bg-[#dcebcf] text-[#356342]"}`}>
                {result.revoked ? "Revoked" : "On-chain record found"}
              </span>
            </div>
            <dl className="grid gap-px bg-[#e9eee6] sm:grid-cols-2">
              <div className="bg-white p-4 sm:col-span-2">
                <dt className="text-[10px] font-semibold uppercase tracking-wider text-[#8b978b]">Credential ID</dt>
                <dd className="mt-2 break-all font-mono text-xs leading-5 text-[#294536]">{result.credential_id}</dd>
              </div>
              <div className="bg-white p-4">
                <dt className="text-[10px] font-semibold uppercase tracking-wider text-[#8b978b]">Network</dt>
                <dd className="mt-2 text-sm font-semibold capitalize text-[#294536]">{result.network}</dd>
              </div>
              <div className="bg-white p-4">
                <dt className="text-[10px] font-semibold uppercase tracking-wider text-[#8b978b]">Issued on</dt>
                <dd className="mt-2 text-sm font-semibold text-[#294536]">
                  {new Date(result.issued_at * 1000).toLocaleString()}
                </dd>
              </div>
              <div className="bg-white p-4 sm:col-span-2">
                <dt className="text-[10px] font-semibold uppercase tracking-wider text-[#8b978b]">Issuer wallet</dt>
                <dd className="mt-2 break-all font-mono text-xs text-[#294536]" title={result.issuer}>{shortAddress(result.issuer)}</dd>
              </div>
              <div className="bg-white p-4 sm:col-span-2">
                <dt className="text-[10px] font-semibold uppercase tracking-wider text-[#8b978b]">Proof commitment</dt>
                <dd className="mt-2 break-all font-mono text-xs leading-5 text-[#294536]">{result.commitment}</dd>
              </div>
            </dl>
            <p className="border-t border-[#e9eee6] bg-[#fbfcf8] px-5 py-3 text-[10px] leading-5 text-[#8b978b]">
              This result confirms the public on-chain record and revocation flag. It does not independently verify the contents of an off-chain certificate.
            </p>
          </section>
        )}
      </div>
      <p className="mt-5 text-center text-[10px] leading-5 text-[#98a197]">
        SOLL Credential · Public verification · No recipient details are requested or displayed
      </p>
    </div>
  );
}
