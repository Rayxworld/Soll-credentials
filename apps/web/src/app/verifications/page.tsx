import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

export default function VerificationsPage() {
  return (
    <DashboardShell>
      <DashboardHeader title="Verifications" />
      <section className="mt-8 rounded-xl border border-gray-200 bg-white p-8">
        <h2 className="text-lg font-semibold">Verification activity</h2>
        <p className="mt-2 text-sm text-gray-500">
          Monitor checks made against credentials issued by your organisation.
        </p>
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="font-medium text-gray-700">No verification activity</p>
          <p className="mt-2 text-sm text-gray-500">
            Verification records will appear here when credentials are checked.
          </p>
        </div>
      </section>
    </DashboardShell>
  );
}
