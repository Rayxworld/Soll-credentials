import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

export default function ProgrammesPage() {
  return (
    <DashboardShell>
      <DashboardHeader title="Programmes" />
      <section className="mt-8 rounded-xl border border-gray-200 bg-white p-8">
        <h2 className="text-lg font-semibold">Manage programmes</h2>
        <p className="mt-2 text-sm text-gray-500">
          Create and manage the courses, training programmes, and events
          under which credentials will be issued.
        </p>
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="font-medium text-gray-700">No programmes yet</p>
          <p className="mt-2 text-sm text-gray-500">
            Programmes will appear here when you create them.
          </p>
        </div>
      </section>
    </DashboardShell>
  );
}
