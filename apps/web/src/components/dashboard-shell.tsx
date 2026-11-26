import Sidebar from "@/components/sidebar";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#f5f5ef] md:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 px-4 py-5 sm:px-7 lg:px-10 lg:py-8">
        <div className="mx-auto w-full max-w-[1440px]">{children}</div>
      </main>
    </div>
  );
}
