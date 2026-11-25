import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

export default function SettingsPage() {
  return (
    <DashboardShell>
      <DashboardHeader title="Organisation settings" />
      <section className="mt-8 rounded-xl border border-gray-200 bg-white p-8">
        <h2 className="text-lg font-semibold">Organisation profile</h2>
        <p className="mt-2 text-sm text-gray-500">
          Manage your organisation details, branding, and issuer information.
        </p>
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="font-medium text-gray-700">Settings unavailable</p>
          <p className="mt-2 text-sm text-gray-500">
            Organisation settings will be available after account setup.
          </p>
        </div>
      </section>
    </DashboardShell>
  );
}
