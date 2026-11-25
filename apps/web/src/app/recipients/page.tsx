import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

export default function RecipientsPage() {
  return (
    <DashboardShell>
      <DashboardHeader title="Recipients" />
      <section className="mt-8 rounded-xl border border-gray-200 bg-white p-8">
        <h2 className="text-lg font-semibold">Manage recipients</h2>
        <p className="mt-2 text-sm text-gray-500">
          Manage the people who receive credentials from your organisation.
        </p>
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="font-medium text-gray-700">No recipients yet</p>
          <p className="mt-2 text-sm text-gray-500">
            Recipients will appear here when you add them.
          </p>
        </div>
      </section>
    </DashboardShell>
  );
}
