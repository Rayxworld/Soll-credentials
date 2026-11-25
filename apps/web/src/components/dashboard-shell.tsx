import Sidebar from "@/components/sidebar";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#f7f8fc] md:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 p-6 md:p-10">
        {children}
      </main>
    </div>
  );
}
