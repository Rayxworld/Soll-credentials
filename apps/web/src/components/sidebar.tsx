"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["Overview", "/", "◫"],
  ["Credentials", "/credentials", "▤"],
  ["Programmes", "/programmes", "⌁"],
  ["Recipients", "/recipients", "◎"],
  ["Verifications", "/verifications", "↗"],
  ["Templates", "/templates", "▧"],
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="relative flex w-full shrink-0 flex-col bg-[#173b30] px-5 py-5 text-[#f4f3e9] print:hidden md:sticky md:top-0 md:h-screen md:w-[252px] md:px-5 md:py-7">
      <Link href="/" className="mb-8 flex items-center gap-3 px-2">
        <span className="grid h-10 w-10 place-items-center rounded-[13px] bg-[#c9ef78] text-xl font-black tracking-[-.12em] text-[#173b30]">S.</span>
        <span>
          <span className="block text-[17px] font-extrabold tracking-[-.035em]">SOLL<span className="text-[#c9ef78]">/</span></span>
          <span className="block text-[9px] font-semibold uppercase tracking-[.2em] text-white/45">Credential infrastructure</span>
        </span>
      </Link>

      <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.2em] text-white/35">Workspace</div>
      <nav className="flex gap-1 overflow-x-auto pb-1 md:flex-col md:overflow-visible" aria-label="Main navigation">
        {links.map(([label, href, glyph]) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href + "/"));
          return (
            <Link key={href} href={href} aria-current={active ? "page" : undefined}
              className={`group flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition md:w-full ${active ? "bg-[#f4f3e9] text-[#173b30] shadow-sm" : "text-white/65 hover:bg-white/[.08] hover:text-white"}`}>
              <span className={`grid h-6 w-6 place-items-center text-base ${active ? "text-[#347454]" : "text-[#c9ef78]/75"}`}>{glyph}</span>
              {label}
              {active && <span className="ml-auto hidden h-1.5 w-1.5 rounded-full bg-[#70a94b] md:block" />}
            </Link>
          );
        })}
      </nav>

      <div className="mt-8 hidden rounded-2xl border border-white/10 bg-white/[.055] p-4 md:block">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase tracking-[.16em] text-white/45">Network status</span>
          <span className="h-2 w-2 rounded-full bg-[#c9ef78]" />
        </div>
        <p className="text-sm font-semibold">Stellar Testnet</p>
        <p className="mt-1 text-[11px] leading-5 text-white/45">Demo environment · not mainnet</p>
      </div>

      <div className="mt-auto hidden border-t border-white/10 pt-5 md:block">
        <Link href="/settings" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] text-white/55 transition hover:bg-white/[.08] hover:text-white">
          <span className="text-base">⚙</span> Organisation settings
        </Link>
        <p className="mt-5 px-3 text-[10px] tracking-wide text-white/25">SOLL CREDENTIAL · TESTNET BUILD</p>
      </div>
    </aside>
  );
}
