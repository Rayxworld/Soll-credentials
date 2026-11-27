import Link from "next/link";
import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

const metrics = [
  { label: "Credentials issued", value: "—", note: "Awaiting API connection", mark: "01" },
  { label: "Currently valid", value: "—", note: "Live registry count", mark: "02" },
  { label: "Revoked", value: "—", note: "Revocation records", mark: "03" },
  { label: "Public checks", value: "—", note: "Verification activity", mark: "04" },
];

const steps = [
  { number: "01", title: "Shape the certificate", detail: "Build a visual identity for every programme.", href: "/templates", action: "Open template studio" },
  { number: "02", title: "Issue with confidence", detail: "Prepare recipient details and credential data.", href: "/credentials", action: "Credential workflow" },
  { number: "03", title: "Make it verifiable", detail: "Anchor a proof and let anyone check its status.", href: "/verifications", action: "Verification desk" },
];

function ActivityMark() {
  return (
    <svg viewBox="0 0 520 132" role="img" aria-label="Illustrative credential activity curve" className="h-full w-full">
      <defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#a8ce7d" stopOpacity=".35"/><stop offset="100%" stopColor="#a8ce7d" stopOpacity="0"/></linearGradient></defs>
      {[22, 56, 90, 124].map(y => <line key={y} x1="0" x2="520" y1={y} y2={y} stroke="#e8ebe3" strokeDasharray="3 6" />)}
      <path d="M0 105 C42 105 46 91 84 91 S128 101 164 75 S220 86 250 60 S306 75 342 47 S402 59 434 28 S488 39 520 13 L520 132 L0 132Z" fill="url(#area)" />
      <path d="M0 105 C42 105 46 91 84 91 S128 101 164 75 S220 86 250 60 S306 75 342 47 S402 59 434 28 S488 39 520 13" fill="none" stroke="#397454" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="434" cy="28" r="4.5" fill="#c9ef78" stroke="#397454" strokeWidth="2"/>
    </svg>
  );
}

export default function Home() {
  return (
    <DashboardShell>
      <DashboardHeader title="Overview" />

      <section className="relative mb-7 overflow-hidden rounded-[26px] bg-[#e7eddf] px-6 py-7 sm:px-9 sm:py-9">
        <div className="relative z-10 max-w-[590px]">
          <p className="mb-4 inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#53745d]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#6c9e4c]"/> Credential operations
          </p>
          <h1 className="max-w-[540px] text-[clamp(30px,4vw,48px)] font-semibold leading-[1.04] tracking-[-.065em] text-[#18392c]">
            Trust, issued.<br/><span className="font-serif font-normal italic text-[#64835d]">Proof that travels.</span>
          </h1>
          <p className="mt-4 max-w-[440px] text-[13px] leading-6 text-[#5c7061]">
            Design credentials, issue them to people, and make every achievement independently verifiable.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/templates" className="rounded-full bg-[#173b30] px-5 py-3 text-[12px] font-semibold text-white transition hover:bg-[#245541]">Design a certificate <span className="ml-2">↗</span></Link>
            <Link href="/verifications" className="rounded-full border border-[#c4d2c0] bg-white/45 px-5 py-3 text-[12px] font-semibold text-[#315542] transition hover:bg-white/80">Explore verification</Link>
          </div>
        </div>
        <div aria-hidden="true" className="pointer-events-none absolute -right-12 -top-24 hidden h-[390px] w-[390px] rounded-full border border-[#c4d3bd] sm:block"/>
        <div aria-hidden="true" className="pointer-events-none absolute -right-1 -top-14 hidden h-[310px] w-[310px] rounded-full border border-[#c4d3bd] sm:block"/>
        <div aria-hidden="true" className="pointer-events-none absolute -right-16 bottom-[-175px] hidden h-[300px] w-[300px] rotate-45 border border-[#b8c9b2] sm:block"/>
        <div className="absolute bottom-6 right-8 hidden rotate-[-7deg] rounded-sm border border-[#d9dfd1] bg-[#fbfbf5] p-3 shadow-[0_20px_50px_rgba(38,66,45,.12)] sm:block lg:right-20">
          <div className="flex h-[132px] w-[190px] flex-col items-center justify-center border border-[#d8dfd0] px-3 text-center">
            <span className="text-[7px] font-bold uppercase tracking-[.25em] text-[#66805e]">SOLL NETWORK</span>
            <span className="mt-3 font-serif text-[20px] italic text-[#233d30]">Certificate</span>
            <span className="mt-1 h-px w-12 bg-[#b7c7ac]"/>
            <span className="mt-3 text-[8px] text-[#7a8878]">AWARDED WITH DISTINCTION</span>
            <span className="mt-2 font-serif text-[14px] text-[#263c30]">Your next achievement</span>
            <span className="mt-3 text-[6px] tracking-[.2em] text-[#8d998a]">DIGITALLY VERIFIABLE</span>
          </div>
        </div>
      </section>

      <section className="mb-7 grid grid-cols-2 gap-3 xl:grid-cols-4">
        {metrics.map((item) => (
          <article key={item.label} className="rounded-[18px] border border-[#e3e7de] bg-[#fbfcf8] p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium text-[#758078]">{item.label}</span>
              <span className="font-mono text-[9px] text-[#b1b9af]">{item.mark}</span>
            </div>
            <p className="mt-4 text-[30px] font-semibold leading-none tracking-[-.06em] text-[#20382c]">{item.value}</p>
            <p className="mt-2 text-[10px] text-[#9aa39a]">{item.note}</p>
          </article>
        ))}
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_.85fr]">
        <section className="rounded-[22px] border border-[#e3e7de] bg-[#fbfcf8] p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#89948a]">Registry pulse</p>
              <h2 className="mt-1 text-[18px] font-semibold tracking-[-.04em] text-[#21382c]">Credential activity</h2>
            </div>
            <span className="rounded-full bg-[#edf2e8] px-3 py-1.5 text-[10px] font-semibold text-[#688064]">Awaiting live data</span>
          </div>
          <div className="mt-5 h-[132px] overflow-hidden rounded-xl bg-[#f5f7f0] px-2 pt-2"><ActivityMark /></div>
          <div className="mt-4 flex items-center justify-between border-t border-[#edf0e9] pt-4">
            <p className="text-[10px] text-[#929b91]">Illustrative visual · API connection pending</p>
            <span className="font-mono text-[10px] text-[#9aa49a]">TESTNET / 01</span>
          </div>
        </section>

        <section className="rounded-[22px] bg-[#173b30] p-5 text-[#f5f4eb] sm:p-6">
          <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#a9c49a]">Your workspace</p>
          <h2 className="mt-2 text-[20px] font-semibold tracking-[-.04em]">SOLL Network</h2>
          <p className="mt-1 text-[11px] text-white/45">Organisation registry</p>
          <div className="my-5 h-px bg-white/10"/>
          <div className="flex items-center justify-between text-[11px]"><span className="text-white/55">Network</span><span className="font-medium">Stellar Testnet</span></div>
          <div className="mt-3 flex items-center justify-between text-[11px]"><span className="text-white/55">Organisation</span><span className="font-medium text-[#c9ef78]">Active on-chain</span></div>
          <div className="mt-3 flex items-center justify-between text-[11px]"><span className="text-white/55">Issuer access</span><span className="font-medium">Demo issuer authorised</span></div>
          <p className="mt-5 rounded-xl border border-white/10 bg-white/[.05] p-3 text-[10px] leading-5 text-white/55">The organisation and demo issuer are registered on Testnet. Application workflows are still being connected.</p>
        </section>
      </div>

      <section className="mt-7">
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#89948a]">A clear path forward</p>
            <h2 className="mt-1 text-[19px] font-semibold tracking-[-.04em] text-[#20382c]">From design to proof</h2>
          </div>
          <span className="hidden text-[10px] text-[#9aa39a] sm:block">SOLL WORKFLOW / 03 STEPS</span>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {steps.map((step) => (
            <article key={step.number} className="group rounded-[18px] border border-[#e3e7de] bg-[#fbfcf8] p-5 transition hover:-translate-y-0.5 hover:border-[#cbd8c6] hover:shadow-[0_12px_30px_rgba(35,58,40,.06)]">
              <span className="font-mono text-[10px] text-[#91a18d]">{step.number} / 03</span>
              <h3 className="mt-4 text-[15px] font-semibold tracking-[-.025em] text-[#263c30]">{step.title}</h3>
              <p className="mt-1.5 min-h-10 text-[11px] leading-5 text-[#849087]">{step.detail}</p>
              <Link href={step.href} className="mt-4 inline-flex items-center gap-2 text-[11px] font-semibold text-[#3d704f] transition group-hover:gap-3">{step.action} <span>↗</span></Link>
            </article>
          ))}
        </div>
      </section>

      <footer className="mt-9 flex flex-wrap justify-between gap-2 border-t border-[#e3e7de] pt-4 text-[9px] tracking-wide text-[#a0a99f]">
        <span>SOLL CREDENTIAL · A MORE TRUSTWORTHY WAY TO RECOGNISE ACHIEVEMENT</span>
        <span>TESTNET PRESENTATION BUILD</span>
      </footer>
    </DashboardShell>
  );
}
