"use client";

import { useMemo, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";

type TemplateStyle = "classic" | "modern" | "minimal";

const presets: { id: TemplateStyle; name: string; description: string; color: string }[] = [
  { id: "classic", name: "Heritage", description: "Formal border and traditional layout", color: "#17345f" },
  { id: "modern", name: "Modern", description: "Bold colour, clean geometry", color: "#3156d8" },
  { id: "minimal", name: "Minimal", description: "Quiet typography and open space", color: "#17766b" },
];

const fieldClass =
  "mt-1.5 w-full rounded-lg border border-[#e1e6dc] bg-[#fbfcf8] px-3 py-2.5 text-sm text-[#304438] outline-none transition focus:border-[#6f9b73] focus:ring-2 focus:ring-[#dce9d0]";

export default function TemplateStudioPage() {
  const [style, setStyle] = useState<TemplateStyle>("classic");
  const [accent, setAccent] = useState("#17345f");
  const [organisation, setOrganisation] = useState("SOLL Network");
  const [certificateTitle, setCertificateTitle] = useState("Certificate of Completion");
  const [recipient, setRecipient] = useState("John Doe");
  const [programme, setProgramme] = useState("Introduction to Cybersecurity");
  const [date, setDate] = useState("26 November 2026");
  const [signatory, setSignatory] = useState("Programme Director");
  const [logo, setLogo] = useState("");
  const [notice, setNotice] = useState("");

  const selectedPreset = useMemo(() => presets.find((item) => item.id === style)!, [style]);

  function choosePreset(id: TemplateStyle) {
    setStyle(id);
    setAccent(presets.find((item) => item.id === id)!.color);
    setNotice("");
  }

  function saveDraft() {
    const draft = {
      style, accent, organisation, certificateTitle, recipient, programme, date, signatory,
    };
    try {
      localStorage.setItem("soll-template-demo-draft", JSON.stringify(draft));
      setNotice("Draft saved on this device.");
    } catch {
      setNotice("Preview updated. Browser storage is unavailable.");
    }
  }

  function uploadLogo(file?: File) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setNotice("Choose an image file for the organisation logo.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setLogo(String(reader.result ?? ""));
      setNotice("Logo added to this preview.");
    };
    reader.readAsDataURL(file);
  }

  return (
    <DashboardShell>
      <div className="print:hidden">
        <DashboardHeader title="Certificate templates" />
      </div>

      <div className="mb-6 flex flex-wrap items-end justify-between gap-3 print:hidden">
        <div>
          <p className="text-sm font-medium text-[#397454]">Template studio</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#20382c]">Design your certificate</h1>
          <p className="mt-1 text-sm text-[#879188]">Make a certificate that reflects your organisation.</p>
        </div>
        <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">
          Demo preview · not yet connected to the API
        </span>
      </div>

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(280px,350px)_minmax(0,1fr)]">
        <section className="space-y-5 print:hidden">
          <div className="rounded-[22px] border border-[#e1e6dc] bg-[#fbfcf8] p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-[#20382c]">Choose a style</h2>
              <span className="text-xs text-[#a4ada2]">01 / 03</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => choosePreset(preset.id)}
                  aria-pressed={style === preset.id}
                  className={`rounded-xl border p-2 text-left transition ${style === preset.id ? "border-[#397454] bg-[#eff4e9] ring-2 ring-[#dce9d0]" : "border-[#e1e6dc] hover:border-slate-300"}`}
                >
                  <span className="mb-2 block h-12 rounded-md border border-black/5" style={{ background: preset.color }}>
                    <span className="mx-auto mt-3 block h-5 w-8 border border-white/70" />
                  </span>
                  <span className="block text-xs font-semibold text-[#304438]">{preset.name}</span>
                </button>
              ))}
            </div>
            <p className="mt-3 text-xs text-[#879188]">{selectedPreset.description}</p>
          </div>

          <div className="rounded-2xl border border-[#e1e6dc] bg-[#fbfcf8] p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-[#20382c]">Certificate details</h2>
              <span className="text-xs text-[#a4ada2]">02 / 03</span>
            </div>
            <label className="block text-xs font-medium text-[#718075]">
              Organisation name
              <input className={fieldClass} value={organisation} onChange={(e) => setOrganisation(e.target.value)} />
            </label>
            <label className="mt-3 block text-xs font-medium text-[#718075]">
              Certificate heading
              <input className={fieldClass} value={certificateTitle} onChange={(e) => setCertificateTitle(e.target.value)} />
            </label>
            <label className="mt-3 block text-xs font-medium text-[#718075]">
              Recipient name
              <input className={fieldClass} value={recipient} onChange={(e) => setRecipient(e.target.value)} />
            </label>
            <label className="mt-3 block text-xs font-medium text-[#718075]">
              Programme / achievement
              <input className={fieldClass} value={programme} onChange={(e) => setProgramme(e.target.value)} />
            </label>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <label className="block text-xs font-medium text-[#718075]">
                Issue date
                <input className={fieldClass} value={date} onChange={(e) => setDate(e.target.value)} />
              </label>
              <label className="block text-xs font-medium text-[#718075]">
                Signatory title
                <input className={fieldClass} value={signatory} onChange={(e) => setSignatory(e.target.value)} />
              </label>
            </div>
          </div>

          <div className="rounded-2xl border border-[#e1e6dc] bg-[#fbfcf8] p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-[#20382c]">Branding</h2>
              <span className="text-xs text-[#a4ada2]">03 / 03</span>
            </div>
            <label className="block text-xs font-medium text-[#718075]">
              Accent colour
              <span className="mt-1.5 flex items-center gap-3 rounded-lg border border-[#e1e6dc] px-3 py-2">
                <input
                  aria-label="Accent colour"
                  type="color"
                  value={accent}
                  onChange={(e) => setAccent(e.target.value)}
                  className="h-8 w-10 cursor-pointer rounded border-0 bg-transparent"
                />
                <span className="font-mono text-xs text-[#879188]">{accent.toUpperCase()}</span>
              </span>
            </label>
            <label className="mt-3 block text-xs font-medium text-[#718075]">
              Organisation logo
              <input
                type="file"
                accept="image/*"
                onChange={(e) => uploadLogo(e.target.files?.[0])}
                className="mt-1.5 block w-full text-xs text-[#879188] file:mr-3 file:rounded-lg file:border-0 file:bg-[#f0f2eb] file:px-3 file:py-2 file:text-xs file:font-semibold file:text-[#53675a] hover:file:bg-slate-200"
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={saveDraft} className="rounded-lg bg-[#173b30] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#245541]">
              Save draft
            </button>
            <button type="button" onClick={() => window.print()} className="rounded-lg border border-[#e1e6dc] bg-[#fbfcf8] px-4 py-2.5 text-sm font-semibold text-[#53675a] transition hover:bg-[#f0f3eb]">
              Print / Save PDF
            </button>
          </div>
          {notice && <p role="status" className="text-xs font-medium text-emerald-700">{notice}</p>}
          <p className="text-xs leading-5 text-[#a4ada2]">This presentation build saves a draft in this browser only. Server-side template storage and PDF generation are not connected yet.</p>
        </section>

        <section className="min-w-0">
          <div className="mb-3 flex items-center justify-between print:hidden">
            <div>
              <h2 className="font-semibold text-[#20382c]">Live preview</h2>
              <p className="text-xs text-[#879188]">Landscape · A4 certificate</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">Live</span>
          </div>

          <div className="rounded-2xl border border-[#e1e6dc] bg-[#f0f2eb] p-3 shadow-inner sm:p-6 print:border-0 print:bg-[#fbfcf8] print:p-0 print:shadow-none">
            <article
              className={`relative mx-auto aspect-[1.414/1] w-full max-w-[900px] overflow-hidden bg-[#fbfcf8] text-center shadow-xl print:shadow-none ${style === "classic" ? "border-[10px]" : style === "minimal" ? "border border-[#e1e6dc]" : "border-0"}`}
              style={{ borderColor: style === "classic" ? accent : undefined }}
            >
              {style === "modern" && <div className="absolute inset-x-0 top-0 h-[13%]" style={{ background: accent }} />}
              {style === "classic" && <div className="absolute inset-2 border border-current opacity-30" style={{ color: accent }} />}
              {style === "modern" && <div className="absolute -right-16 top-10 h-44 w-44 rotate-45 opacity-10" style={{ background: accent }} />}
              <div className={`relative flex h-full flex-col items-center justify-center px-[7%] py-[5%] ${style === "modern" ? "pt-[14%]" : ""}`}>
                <div className="mb-[2%] flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-2 text-lg font-bold sm:h-16 sm:w-16 sm:text-2xl" style={{ borderColor: accent, color: accent }}>
                  {logo ? <span aria-label="Organisation logo" role="img" className="h-full w-full bg-contain bg-center bg-no-repeat" style={{ backgroundImage: `url(${logo})` }} /> : <span>{organisation.trim().charAt(0) || "S"}</span>}
                </div>
                <p className="text-[clamp(8px,1.3vw,13px)] font-semibold uppercase tracking-[0.2em]" style={{ color: accent }}>{organisation || "Your organisation"}</p>
                <div className="my-[2%] h-px w-1/4" style={{ background: accent, opacity: 0.45 }} />
                <p className="text-[clamp(9px,1.7vw,17px)] font-medium text-[#879188]">{certificateTitle || "Certificate of Achievement"}</p>
                <p className="mt-[2%] font-serif text-[clamp(22px,5vw,48px)] leading-tight text-[#20382c]">{recipient || "Recipient name"}</p>
                <p className="mt-[2%] max-w-[80%] text-[clamp(8px,1.5vw,14px)] leading-relaxed text-[#718075]">
                  has successfully completed the programme
                </p>
                <p className="mt-[1%] max-w-[85%] font-semibold text-[clamp(11px,2vw,20px)]" style={{ color: accent }}>{programme || "Programme title"}</p>
                <p className="mt-[3%] text-[clamp(8px,1.3vw,13px)] text-[#879188]">Awarded on {date || "Issue date"}</p>
                <div className="mt-[4%] flex w-full items-end justify-between gap-4 px-[4%]">
                  <div className="w-[32%] border-t border-[#aeb9aa] pt-1.5 text-left">
                    <p className="text-[clamp(7px,1.1vw,11px)] font-semibold text-[#304438]">{signatory || "Authorised signatory"}</p>
                    <p className="text-[clamp(6px,0.9vw,9px)] text-[#879188]">Authorised signature</p>
                  </div>
                  <div className="hidden text-center sm:block">
                    <div className="mx-auto grid h-10 w-10 grid-cols-3 gap-0.5 border border-slate-300 p-1 opacity-70">
                      {Array.from({ length: 9 }).map((_, index) => <span key={index} className={index % 2 === 0 ? "bg-slate-700" : "bg-slate-200"} />)}
                    </div>
                    <p className="mt-1 text-[8px] text-[#a4ada2]">Verify credential</p>
                  </div>
                  <div className="w-[32%] border-t border-[#aeb9aa] pt-1.5 text-right">
                    <p className="text-[clamp(7px,1.1vw,11px)] font-semibold text-[#304438]">{organisation || "Issuing organisation"}</p>
                    <p className="text-[clamp(6px,0.9vw,9px)] text-[#879188]">Issuing authority</p>
                  </div>
                </div>
                <p className="absolute bottom-[2%] text-[clamp(6px,0.9vw,9px)] tracking-wider text-[#a4ada2]">SOLL CREDENTIAL · DIGITAL CERTIFICATE</p>
              </div>
            </article>
          </div>
          <p className="mt-3 text-center text-xs text-[#a4ada2] print:hidden">The preview updates as you edit the fields.</p>
        </section>
      </div>
    </DashboardShell>
  );
}
