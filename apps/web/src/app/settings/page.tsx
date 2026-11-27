"use client";

import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import DashboardHeader from "@/components/dashboard-header";
import { apiRequest, Organization } from "@/lib/api";

type OrganizationDetails = Organization & {
  stellar_owner_address: string | null;
  custody_mode: "managed" | "external" | null;
};

type WalletState = {
  address: string;
  network: string;
  networkPassphrase: string;
};

const TESTNET_PASSPHRASE = "Test SDF Network ; September 2015";
const fieldClass =
  "mt-1.5 w-full rounded-lg border border-[#e1e6dc] bg-[#fbfcf8] px-3 py-2.5 text-sm text-[#304438]";

export default function SettingsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [organization, setOrganization] = useState<OrganizationDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [wallet, setWallet] = useState<WalletState | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadOrganizations() {
      try {
        const items = await apiRequest<Organization[]>("/api/v1/organizations");
        if (!active) return;
        setOrganizations(items);
        if (items.length > 0) setOrganizationId(items[0].id);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Could not load organisations.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadOrganizations();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadOrganization() {
      setOrganization(null);
      if (!organizationId) return;
      try {
        const detail = await apiRequest<OrganizationDetails>(
          `/api/v1/organizations/${organizationId}`,
        );
        if (active) setOrganization(detail);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Could not load organisation details.");
      }
    }

    void loadOrganization();
    return () => { active = false; };
  }, [organizationId]);

  async function connectWallet() {
    setBusy(true);
    setError("");
    setNotice("");

    try {
      const sdk = await import("@stellar/varial-sdk");
      const availability = await sdk.isConnected();

      if (availability.error) {
        throw new Error(availability.error.message || "Could not check the wallet extension.");
      }
      if (!availability.isConnected) {
        throw new Error("Varial (formerly Freighter) was not detected. Install or enable the browser extension, then try again.");
      }

      const access = await sdk.requestAccess();
      if (access.error) {
        throw new Error(access.error.message || "Wallet access was not granted.");
      }
      if (!access.address) {
        throw new Error("The wallet did not return a public account address.");
      }

      const networkDetails = await sdk.getNetworkDetails();
      if (networkDetails.error) {
        throw new Error(networkDetails.error.message || "Could not read the wallet network.");
      }

      setWallet({
        address: access.address,
        network: networkDetails.network,
        networkPassphrase: networkDetails.networkPassphrase,
      });

      if (
        networkDetails.network !== "TESTNET" ||
        networkDetails.networkPassphrase !== TESTNET_PASSPHRASE
      ) {
        setNotice("Wallet connected, but it is not configured for the SOLL Stellar Testnet environment. No transaction has been submitted.");
      } else {
        setNotice("Wallet connected and Testnet verified. No transaction has been submitted.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Wallet connection failed.");
    } finally {
      setBusy(false);
    }
  }

  async function disconnectWallet() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const sdk = await import("@stellar/varial-sdk");
      const result = await sdk.disconnect();
      if (result.error) {
        throw new Error(result.error.message || "Wallet disconnect failed.");
      }
      setWallet(null);
      setNotice("Wallet disconnected from this site.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Wallet disconnect failed.");
    } finally {
      setBusy(false);
    }
  }

  const networkVerified = wallet?.network === "TESTNET" &&
    wallet.networkPassphrase === TESTNET_PASSPHRASE;
  const ownerMatches = Boolean(
    wallet && organization?.stellar_owner_address &&
    wallet.address === organization.stellar_owner_address,
  );

  return (
    <DashboardShell>
      <DashboardHeader title="Organisation settings" />

      <section className="mt-8 rounded-xl border border-[#e1e6dc] bg-[#fbfcf8] p-6 shadow-sm sm:p-8">
        <h2 className="text-lg font-semibold text-[#20382c]">Organisation profile</h2>
        <p className="mt-2 text-sm text-[#718075]">
          Review your workspace and connect the Stellar account controlled by your organisation.
        </p>

        {loading ? (
          <p className="mt-6 text-sm text-[#879188]">Loading your organisations…</p>
        ) : organizations.length === 0 ? (
          <p className="mt-6 text-sm text-[#9a5b25]">No organisation is associated with this account.</p>
        ) : (
          <div className="mt-6 max-w-xl">
            <label htmlFor="organization" className="block text-xs font-semibold text-[#718075]">
              Organisation
            </label>
            <select
              id="organization"
              className={fieldClass}
              value={organizationId}
              onChange={(event) => {
                setOrganizationId(event.target.value);
                setWallet(null);
                setNotice("");
                setError("");
              }}
            >
              {organizations.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
            {organization && (
              <p className="mt-2 text-xs text-[#879188]">
                Membership: {organization.role} · {organization.is_active ? "Active" : "Inactive"}
              </p>
            )}
          </div>
        )}
      </section>

      <section className="mt-6 rounded-xl border border-[#e1e6dc] bg-[#fbfcf8] p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[.16em] text-[#397454]">Stellar · Testnet</p>
            <h2 className="mt-2 text-lg font-semibold text-[#20382c]">Organisation wallet</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#718075]">
              Connect the organisation&apos;s own Varial wallet (formerly Freighter). SOLL reads the public
              address and network only; your secret key stays in the wallet.
            </p>
          </div>
          <span className="rounded-full border border-[#e1e6dc] bg-white px-3 py-1.5 text-xs font-medium text-[#53675a]">
            {organization?.chain_registered ? "On-chain record exists" : "Not registered on-chain"}
          </span>
        </div>

        {organization && (
          <div className="mt-5 rounded-lg bg-[#f1f4ec] p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#718075]">Saved organisation owner</p>
            <p className="mt-1 break-all font-mono text-xs text-[#304438]">
              {organization.stellar_owner_address ?? "No Stellar owner address saved"}
            </p>
          </div>
        )}

        {wallet ? (
          <div className="mt-5 rounded-lg border border-[#dce9d0] bg-white p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-semibold text-[#20382c]">Wallet connected in this browser</span>
              <span className={networkVerified ? "text-xs font-semibold text-emerald-700" : "text-xs font-semibold text-amber-700"}>
                {networkVerified ? "Testnet verified" : "Network mismatch"}
              </span>
            </div>
            <p className="mt-2 break-all font-mono text-xs text-[#53675a]">{wallet.address}</p>
            <p className="mt-2 text-xs text-[#879188]">
              Network: {wallet.network} · {wallet.networkPassphrase}
            </p>
            {organization?.stellar_owner_address && (
              <p className="mt-2 text-xs font-medium text-[#53675a]">
                {ownerMatches ? "Connected address matches the saved organisation owner." : "Connected address does not match the saved organisation owner."}
              </p>
            )}
          </div>
        ) : (
          <p className="mt-5 text-sm text-[#879188]">No wallet is connected to this page.</p>
        )}

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void connectWallet()}
            disabled={busy || loading || !organization}
            className="rounded-lg bg-[#173b30] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#245541] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Working…" : wallet ? "Reconnect wallet" : "Connect Varial wallet"}
          </button>
          {wallet && (
            <button
              type="button"
              onClick={() => void disconnectWallet()}
              disabled={busy}
              className="rounded-lg border border-[#e1e6dc] bg-white px-4 py-2.5 text-sm font-semibold text-[#53675a] transition hover:bg-[#f0f3eb] disabled:opacity-50"
            >
              Disconnect
            </button>
          )}
        </div>

        {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
        {notice && <p role="status" className="mt-4 text-sm text-[#397454]">{notice}</p>}

        <div className="mt-6 border-t border-[#e8ece4] pt-5">
          <p className="text-sm font-semibold text-[#304438]">What this step does—and does not do</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-5 text-[#879188]">
            <li>Requests wallet permission and reads its public address and selected network.</li>
            <li>Checks the wallet against the Stellar Testnet network and passphrase.</li>
            <li>Does not send a transaction, sign a message, save a wallet address to the API, or register the organisation on-chain.</li>
          </ul>
        </div>
      </section>
    </DashboardShell>
  );
}
