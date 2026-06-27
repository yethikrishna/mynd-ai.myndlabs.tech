"use client";

import React, { useState } from "react";
import useSWR from "swr";
import { errorHandlingFetcher } from "@/lib/fetcher";
import Button from "@/refresh-components/buttons/Button";
import Text from "@/refresh-components/texts/Text";
import { Card } from "@/refresh-components/cards";
import {
  credentialsKey,
  deleteCredential,
  providersKey,
  startOAuth,
  upsertCredential,
} from "../api";
import type {
  CredentialScope,
  CredentialSummary,
  ProviderMeta,
} from "../types";

type Tab = "defaults" | "byok";

/**
 * /<slug>/settings/models — model settings.
 *
 *  • "Use platform defaults": explains that admin/system keys are used.
 *  • "Bring your own key": add per-user (or, for admins, per-org) provider keys,
 *    optional base URL for OpenAI-compatible/proxy/local endpoints, and OAuth
 *    "Connect" for providers that support it.
 */
export function ModelSettingsPage() {
  const [tab, setTab] = useState<Tab>("defaults");

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-8">
      <Text headingH1>Model settings</Text>

      <div className="flex gap-2">
        <Button
          action
          primary={tab === "defaults"}
          secondary={tab !== "defaults"}
          onClick={() => setTab("defaults")}
        >
          Use platform defaults
        </Button>
        <Button
          action
          primary={tab === "byok"}
          secondary={tab !== "byok"}
          onClick={() => setTab("byok")}
        >
          Bring your own key
        </Button>
      </div>

      {tab === "defaults" ? <PlatformDefaults /> : <BringYourOwnKey />}
    </div>
  );
}

function PlatformDefaults() {
  return (
    <Card>
      <Text headingH3>Platform defaults</Text>
      <Text text03 secondaryBody>
        This product uses the LLM providers configured by your administrator. No
        action is needed. To use your own provider account instead, switch to
        “Bring your own key”.
      </Text>
    </Card>
  );
}

function BringYourOwnKey() {
  const { data: providerData } = useSWR<{ providers: ProviderMeta[] }>(
    providersKey,
    errorHandlingFetcher
  );
  const providers = providerData?.providers ?? [];

  // Most users manage their own keys; admins can also manage org-wide keys.
  const [scope, setScope] = useState<CredentialScope>("user");
  const {
    data: creds,
    mutate,
  } = useSWR<CredentialSummary[]>(credentialsKey(scope), errorHandlingFetcher);

  const [provider, setProvider] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const selected = providers.find((p) => p.name === provider);

  async function save() {
    if (!provider || !apiKey) {
      setMsg("Select a provider and enter an API key.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      await upsertCredential(scope, {
        provider_name: provider,
        api_key: apiKey,
        base_url: baseUrl || undefined,
        is_default: true,
      });
      setApiKey("");
      setBaseUrl("");
      setMsg("Saved.");
      mutate();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed to save.");
    } finally {
      setBusy(false);
    }
  }

  async function connectOAuth(p: string) {
    try {
      const { authorize_url } = await startOAuth(p);
      window.location.href = authorize_url;
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed to start OAuth.");
    }
  }

  async function remove(id: string) {
    await deleteCredential(scope, id);
    mutate();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        <Button
          action
          primary={scope === "user"}
          secondary={scope !== "user"}
          size="md"
          onClick={() => setScope("user")}
        >
          My keys
        </Button>
        <Button
          action
          primary={scope === "org"}
          secondary={scope !== "org"}
          size="md"
          onClick={() => setScope("org")}
        >
          Organization keys
        </Button>
      </div>

      <Card>
        <Text headingH3>Add a provider key</Text>

        <label className="flex flex-col gap-1">
          <Text text03 secondaryBody>
            Provider
          </Text>
          <select
            className="rounded-08 border border-border-01 bg-transparent p-2"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="">Select a provider…</option>
            {providers.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <Text text03 secondaryBody>
            API key
          </Text>
          <input
            type="password"
            autoComplete="off"
            className="rounded-08 border border-border-01 bg-transparent p-2"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-…"
          />
        </label>

        {selected?.supports_base_url && (
          <label className="flex flex-col gap-1">
            <Text text03 secondaryBody>
              Base URL (optional)
            </Text>
            <input
              type="text"
              className="rounded-08 border border-border-01 bg-transparent p-2"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://my-proxy.internal/v1"
            />
          </label>
        )}

        <div className="flex items-center gap-3">
          <Button main primary onClick={save} disabled={busy}>
            {busy ? "Saving…" : "Save key"}
          </Button>
          {selected?.supports_oauth && (
            <Button
              action
              secondary
              onClick={() => connectOAuth(selected.name)}
            >
              Connect {selected.name} via OAuth
            </Button>
          )}
          {msg && (
            <Text text03 secondaryBody>
              {msg}
            </Text>
          )}
        </div>
      </Card>

      <Card>
        <Text headingH3>
          {scope === "user" ? "My configured keys" : "Organization keys"}
        </Text>
        {!creds || creds.length === 0 ? (
          <Text text03 secondaryBody>
            No keys configured yet.
          </Text>
        ) : (
          <div className="flex flex-col gap-2">
            {creds.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded-08 border border-border-01 p-2"
              >
                <Text text02 mainUiBody>
                  {c.provider_name}
                  {c.is_default ? " · default" : ""}
                  {c.base_url ? ` · ${c.base_url}` : ""} · {c.credential_type}
                </Text>
                <Button action tertiary danger onClick={() => remove(c.id)}>
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default ModelSettingsPage;
