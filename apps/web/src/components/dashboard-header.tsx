"use client";

export default function DashboardHeader({ title }: { title: string }) {
  return (
    <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-[#e3e6dd] pb-5 print:hidden">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[.19em] text-[#879188]"><strong className="font-extrabold text-[#526b5a]">SOLL</strong> Network <span className="px-1 text-[#bdc5ba]">/</span> Workspace</p>
        <h2 className="mt-1.5 text-[22px] font-semibold tracking-[-.045em] text-[#17251f]">{title}</h2>
      </div>
      <div className="flex items-center gap-3">
        <span className="rounded-full border border-[#dfe5d9] bg-[#fbfcf8] px-3 py-2 text-[11px] font-semibold text-[#557061]">TESTNET</span>
        <div className="grid h-9 w-9 place-items-center rounded-full bg-[#dce8d6] text-xs font-bold text-[#285640]">S</div>
      </div>
    </header>
  );
}
