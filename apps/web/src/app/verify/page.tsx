import Link from "next/link";
import CredentialVerifier from "@/components/credential-verifier";

export const metadata = {
  title: "Verify a credential | SOLL",
  description: "Independently check a SOLL credential's public on-chain record.",
};

export default function VerifyPage() {
  return (
    <main className="min-h-screen bg-[#f5f5ef] px-4 py-8 sm:px-6 sm:py-12">
      <header className="mx-auto mb-10 flex w-full max-w-5xl items-center justify-between">
        <Link href="/" className="flex items-center gap-3" aria-label="SOLL Credential home">
          <span className="grid h-10 w-10 place-items-center rounded-[13px] bg-[#c9ef78] text-xl font-black tracking-[-.12em] text-[#173b30]">S.</span>
          <span>
            <span className="block text-[17px] font-extrabold tracking-[-.035em] text-[#173b30]">SOLL</span>
            <span className="block text-[9px] font-semibold uppercase tracking-[.2em] text-[#849184]">Credential infrastructure</span>
          </span>
        </Link>
        <span className="rounded-full border border-[#dce4d9] bg-white/70 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#718273]">
          Public verifier
        </span>
      </header>
      <CredentialVerifier />
      <footer className="mx-auto mt-12 max-w-5xl border-t border-[#e2e7df] pt-5 text-center text-[10px] text-[#9aa39a]">
        © SOLL Credential. Built for verifiable achievement.
      </footer>
    </main>
  );
}
