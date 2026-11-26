"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["Overview", "/"],
  ["Credentials", "/credentials"],
  ["Templates", "/templates"],
  ["Programmes", "/programmes"],
  ["Recipients", "/recipients"],
  ["Verifications", "/verifications"],
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-full bg-[#111a32] p-6 text-white md:min-h-screen md:w-64 md:shrink-0">
      <Link href="/" className="mb-12 block">
        <h1 className="text-xl font-bold">SOLL<span className="text-indigo-400">.</span></h1>
        <p className="mt-1 text-xs text-slate-400">CREDENTIAL MANAGEMENT</p>
      </Link>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Workspace</p>
      <nav className="space-y-2">
        {links.map(([label, href]) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href} aria-current={active ? "page" : undefined}
              className={`block rounded-lg px-4 py-3 text-sm ${active ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-white/10"}`}>
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-12 border-t border-white/10 pt-5">
        <Link href="/settings" className={`text-sm ${pathname === "/settings" ? "text-white" : "text-slate-300 hover:text-white"}`}>
          Organisation settings
        </Link>
      </div>
    </aside>
  );
}
