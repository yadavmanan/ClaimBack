import { useState, useEffect } from "react";
import type { VaultDocument } from "../../types/models";
import { Badge } from "./Badge";
import {
  CloseIcon,
  DocumentIcon,
  ShieldIcon,
  CheckIcon,
  ExternalLinkIcon,
  DownloadIcon,
  AgentIcon,
} from "../icons";

interface DocumentViewerModalProps {
  document: VaultDocument | null;
  onClose: () => void;
}

export function DocumentViewerModal({ document, onClose }: DocumentViewerModalProps) {
  const [activeTab, setActiveTab] = useState<"pdf" | "ocr">("pdf");

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!document) return null;

  const facts = document.normalized_facts || {};
  const hasPreview = Boolean(document.preview_url);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative flex h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-hairline bg-cream shadow-2xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <header className="flex shrink-0 items-center justify-between border-b border-hairline bg-cream-100/90 px-6 py-3.5 backdrop-blur-md">
          <div className="flex items-center gap-3 min-w-0">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cream-200 text-ink">
              {document.doc_type === "WARRANTY" || document.doc_type === "POLICY" ? (
                <ShieldIcon width={16} height={16} />
              ) : (
                <DocumentIcon width={16} height={16} />
              )}
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-semibold text-ink truncate leading-snug">
                  {document.title}
                </h2>
                <Badge tone={document.doc_type === "WARRANTY" ? "forest" : "neutral"}>
                  {document.doc_type}
                </Badge>
                <span className="inline-flex items-center gap-1 rounded-full bg-forest-soft px-2 py-0.5 text-[10px] font-semibold text-forest">
                  <CheckIcon width={11} height={11} />
                  {Math.round(document.confidence_score * 100)}% Verified
                </span>
              </div>
              <p className="text-xs text-ink-faint truncate">
                Issuer: <span className="font-medium text-ink-soft">{document.vendor_or_issuer}</span> • Added{" "}
                {new Date(document.uploaded_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {hasPreview && (
              <>
                <a
                  href={document.preview_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-hairline bg-white/70 px-2.5 py-1.5 text-xs font-medium text-ink transition-colors hover:bg-cream-200"
                  title="Open in new window"
                >
                  <ExternalLinkIcon width={14} height={14} />
                  <span className="hidden sm:inline">Open</span>
                </a>
                <a
                  href={document.preview_url}
                  download={document.file_name || "document.pdf"}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-hairline bg-white/70 px-2.5 py-1.5 text-xs font-medium text-ink transition-colors hover:bg-cream-200"
                  title="Download file"
                >
                  <DownloadIcon width={14} height={14} />
                  <span className="hidden sm:inline">Download</span>
                </a>
              </>
            )}

            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-hairline bg-white/70 text-ink transition-colors hover:bg-cream-200"
              aria-label="Close modal"
            >
              <CloseIcon width={16} height={16} />
            </button>
          </div>
        </header>

        {/* Content Split: Left (PDF / Preview), Right (AI Facts & Audit) */}
        <div className="grid flex-1 grid-cols-1 overflow-hidden lg:grid-cols-12">
          {/* Left Column: PDF Preview / Document Viewer (7 cols) */}
          <div className="flex flex-col border-b border-hairline lg:col-span-7 lg:border-b-0 lg:border-r bg-cream-100/30 overflow-hidden">
            {/* View switcher bar */}
            <div className="flex items-center justify-between border-b border-hairline bg-white/50 px-4 py-2">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setActiveTab("pdf")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    activeTab === "pdf"
                      ? "bg-forest text-white"
                      : "text-ink-soft hover:bg-cream-200 hover:text-ink"
                  }`}
                >
                  Original Document (PDF)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("ocr")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    activeTab === "ocr"
                      ? "bg-forest text-white"
                      : "text-ink-soft hover:bg-cream-200 hover:text-ink"
                  }`}
                >
                  Raw OCR Text
                </button>
              </div>

              <span className="text-[11px] font-mono text-ink-faint">
                {document.file_name || `${document.doc_type.toLowerCase()}_source.pdf`}
              </span>
            </div>

            {/* Document display area */}
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center">
              {activeTab === "pdf" ? (
                hasPreview ? (
                  <div className="h-full w-full rounded-xl border border-hairline bg-white shadow-xs overflow-hidden">
                    <iframe
                      src={`${document.preview_url}#toolbar=1&navpanes=0&view=FitH`}
                      title={document.title}
                      className="h-full w-full border-0"
                    />
                  </div>
                ) : (
                  /* Fallback High-Fidelity Digital Statement for simulated documents */
                  <div className="h-full w-full max-w-lg rounded-xl border border-hairline bg-white p-6 shadow-sm overflow-y-auto text-ink">
                    <div className="flex items-start justify-between border-b border-hairline pb-4">
                      <div>
                        <span className="text-xs font-semibold uppercase tracking-wider text-forest">
                          {document.doc_type}
                        </span>
                        <h3 className="font-display text-lg font-bold text-ink">{document.vendor_or_issuer}</h3>
                        <p className="text-xs text-ink-faint font-mono">Source ID: {document.doc_id}</p>
                      </div>
                      <div className="rounded-lg bg-cream-100 px-3 py-1.5 text-right font-mono">
                        <div className="text-[10px] text-ink-faint uppercase">Status</div>
                        <div className="text-xs font-bold text-forest">AUTHENTICATED</div>
                      </div>
                    </div>

                    <div className="mt-4 space-y-3">
                      <div className="text-xs font-medium text-ink-soft">Extracted Line Items & Facts:</div>
                      <div className="rounded-lg border border-hairline bg-cream/40 p-3 font-mono text-xs space-y-1.5">
                        {Object.entries(facts).map(([key, value]) => (
                          <div key={key} className="flex justify-between border-b border-hairline/50 pb-1 last:border-b-0 last:pb-0">
                            <span className="text-ink-faint">{key}:</span>
                            <span className="font-semibold text-ink">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="mt-6 rounded-lg border border-dashed border-forest/30 bg-forest-soft/40 p-3 text-center">
                      <p className="text-xs text-forest font-medium">
                        🛡️ Cryptographically signed and verified in user vault
                      </p>
                    </div>
                  </div>
                )
              ) : (
                /* Raw OCR Text tab */
                <div className="h-full w-full overflow-auto rounded-xl border border-hairline bg-white p-4 font-mono text-xs text-ink-soft leading-relaxed select-text">
                  <pre className="whitespace-pre-wrap font-mono">
                    {document.raw_ocr_text ||
                      JSON.stringify(
                        {
                          document_id: document.doc_id,
                          type: document.doc_type,
                          issuer: document.vendor_or_issuer,
                          facts: document.normalized_facts,
                          confidence: document.confidence_score,
                          vault_uri: document.s3_uri,
                        },
                        null,
                        2
                      )}
                  </pre>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: AI Extraction & Fact Sheet (5 cols) */}
          <div className="flex flex-col lg:col-span-5 overflow-y-auto p-5 bg-white/70">
            {/* Agent Analysis Banner */}
            <div className="rounded-xl border border-hairline bg-cream-100/70 p-3.5 mb-4">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-forest text-white">
                  <AgentIcon width={12} height={12} />
                </span>
                <span className="text-xs font-bold text-ink">Strands Parser Agent</span>
                <span className="ml-auto text-[10px] font-mono text-forest font-semibold">
                  AWS Bedrock Claude 3.7
                </span>
              </div>
              <p className="text-xs text-ink-soft leading-relaxed">
                Extracted key commercial entities, line item charges, and validation dates with{" "}
                <span className="font-semibold text-forest">
                  {Math.round(document.confidence_score * 100)}% certainty
                </span>
                .
              </p>
            </div>

            {/* Financial Highlight Card */}
            {Boolean(facts.total_amount) && (
              <div className="mb-4 rounded-xl border border-hairline bg-gradient-to-br from-cream to-cream-100 p-4">
                <div className="text-[11px] font-medium uppercase tracking-wider text-ink-faint">
                  Total Document Amount
                </div>
                <div className="mt-1 font-sans text-2xl font-bold text-ink tracking-tight">
                  {facts.currency === "₹ (INR)" || String(facts.total_amount).includes("₹")
                    ? `₹${facts.total_amount}`
                    : `$${Number(facts.total_amount).toFixed(2)}`}
                </div>
                {Boolean(facts.billing_cycle || facts.expiration_date) && (
                  <div className="mt-1 text-xs text-ink-soft">
                    {facts.billing_cycle ? (
                      <>Cycle: <span className="font-mono font-medium text-ink">{String(facts.billing_cycle)}</span></>
                    ) : (
                      <>Valid through: <span className="font-mono font-medium text-ink">{String(facts.expiration_date)}</span></>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Structured Facts Table */}
            <div className="mb-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink-faint mb-2">
                Extracted Fact Sheet
              </h4>
              <div className="rounded-xl border border-hairline bg-white divide-y divide-hairline text-xs">
                {Object.entries(facts).map(([key, val]) => {
                  const label = key
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (l) => l.toUpperCase());
                  return (
                    <div key={key} className="flex items-start justify-between p-2.5">
                      <span className="font-medium text-ink-soft shrink-0 mr-3">{label}</span>
                      <span className="font-mono text-ink text-right break-all">
                        {typeof val === "object" ? JSON.stringify(val) : String(val)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ClaimBack Automated Audit Status */}
            <div className="mt-auto pt-2">
              <div className="rounded-xl border border-hairline bg-cream-100/50 p-3 text-xs">
                <div className="flex items-center gap-1.5 font-semibold text-ink mb-1">
                  <ShieldIcon width={14} height={14} className="text-forest" />
                  ClaimBack Protection Engine
                </div>
                <p className="text-ink-soft leading-snug text-[11px]">
                  Document is actively monitored against your vault. Any unexpected rate hikes, double billing, or unapplied warranty claims will trigger an instant alert.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
