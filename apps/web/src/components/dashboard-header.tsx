export default function DashboardHeader({ title }: { title: string }) {
  return (
    <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-sm text-slate-500">Workspace / {title}</p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight">{title}</h2>
      </div>
      <div className="flex items-center gap-3">
        <span className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm">
          My organisation
        </span>
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 font-semibold text-indigo-700">
          O
        </div>
      </div>
    </header>
  );
}
