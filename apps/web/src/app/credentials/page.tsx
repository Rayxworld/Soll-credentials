import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

export default function CredentialsPage() {
  return (
    <DashboardShell>
      <DashboardHeader title="Credentials" />
      <section className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Issued credentials</h3>
          <p className="mt-1 text-sm text-slate-500">Create, manage and track your organisation&apos;s credentials.</p>
        </div>
        <button disabled className="rounded-lg bg-indigo-600 px-5 py-3 text-sm font-medium text-white opacity-60">
          + Issue credential
        </button>
      </section>
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <input disabled placeholder="Search credentials..." className="w-full max-w-sm rounded-lg border border-slate-200 px-4 py-2.5 text-sm" />
          <select disabled className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm text-slate-500">
            <option>All statuses</option>
            <option>Active</option>
            <option>Revoked</option>
          </select>
        </div>
        <div className="flex min-h-72 flex-col items-center justify-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-50 text-2xl text-indigo-600">◇</div>
          <h3 className="font-semibold">No credentials yet</h3>
          <p className="mt-2 max-w-md text-sm text-slate-500">
            Credentials issued by your organisation will appear here. Set up your programmes and recipients before issuing.
          </p>
        </div>
      </section>
    </DashboardShell>
  );
}
