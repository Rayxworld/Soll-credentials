import Link from "next/link";
import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

export default function VerificationsPage() {
  return (
    <DashboardShell>
      <DashboardHeader title="Verifications" />
      <section className="mt-8 rounded-[22px] border border-[#e2e8de] bg-[#fbfcf8] p-6 sm:p-8">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
          <div className="max-w-xl">
            <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#7e907d]">Public verification</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-.05em] text-[#1d3d2f]">Check a credential against the registry.</h2>
            <p className="mt-3 text-sm leading-6 text-[#78857a]">
              Anyone with a SOLL credential ID can check its public on-chain record and revocation status. Recipient details are never shown by this check.
            </p>
            <Link href="/verify" className="mt-5 inline-flex items-center gap-2 rounded-full bg-[#173b30] px-5 py-3 text-xs font-semibold text-white transition hover:bg-[#285742]">
              Open public verifier <span aria-hidden="true">↗</span>
            </Link>
          </div>
          <div className="grid h-28 w-28 shrink-0 place-items-center self-center rounded-full border border-[#dce7d5] bg-[#f0f5eb] sm:self-auto">
            <span className="text-4xl text-[#4d7655]" aria-hidden="true">✓</span>
          </div>
        </div>
      </section>

      <section className="mt-5 rounded-[22px] border border-[#e2e8de] bg-[#fbfcf8] p-6">
        <h2 className="text-base font-semibold text-[#294334]">Verification activity</h2>
        <p className="mt-2 text-sm leading-6 text-[#89948a]">
          Check analytics will appear here after verification events are persisted by the API. The current public verifier performs live read-only registry checks and does not yet store visitor activity.
        </p>
      </section>
    </DashboardShell>
  );
}
