import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

const metrics = [
  ["Total credentials", "—", "Credentials issued"],
  ["Active credentials", "—", "Currently valid"],
  ["Revoked credentials", "—", "Revocation records"],
  ["Verifications", "—", "Public verification activity"],
];

export default function Home() {
  return (
    <DashboardShell>
      <DashboardHeader title="Overview" />
      <section className="mb-8">
        <h3 className="text-lg font-semibold">Welcome to SOLL Credential</h3>
        <p className="mt-1 text-sm text-slate-500">
          Manage your organisation&apos;s digital credentials from one place.
        </p>
      </section>
      <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(([label, value, note]) => (
          <article key={label} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-4 text-3xl font-bold">{value}</p>
            <p className="mt-2 text-xs text-slate-400">{note}</p>
          </article>
        ))}
      </section>
      <section className="mt-8 grid gap-5 xl:grid-cols-3">
        <article className="rounded-xl border border-slate-200 bg-white p-6 xl:col-span-2">
          <h3 className="font-semibold">Credential activity</h3>
          <p className="mt-2 text-sm text-slate-500">
            Your issuance activity will appear here once credentials are issued.
          </p>
          <div className="mt-8 flex h-40 items-center justify-center rounded-lg border border-dashed border-slate-200 text-sm text-slate-400">
            No activity yet
          </div>
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="font-semibold">Quick actions</h3>
          <div className="mt-5 space-y-3">
            {["Issue a credential", "Add recipients", "Create a programme"].map(item => (
              <button key={item} className="w-full rounded-lg border border-slate-200 px-4 py-3 text-left text-sm font-medium hover:border-indigo-300 hover:bg-indigo-50">
                {item} <span className="float-right text-slate-400">→</span>
              </button>
            ))}
          </div>
        </article>
      </section>
      <p className="mt-10 text-xs text-slate-400">SOLL Credential · Dashboard preview</p>
    </DashboardShell>
  );
}
