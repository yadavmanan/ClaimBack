import { useEffect, useState } from "react";
import { useClaimBackStore } from "../hooks/useClaimBackStore";
import { DocumentIcon, ShieldIcon, EyeIcon } from "../components/icons";
import { formatDate } from "../lib/format";
import { Badge } from "../components/ui/Badge";
import { UploadDropzone } from "../components/ui/UploadDropzone";
import { DocumentViewerModal } from "../components/ui/DocumentViewerModal";
import type { VaultDocument } from "../types/models";

const docTypeMeta: Record<string, { tone: "neutral" | "forest" | "alert"; icon: typeof DocumentIcon }> = {
  RECEIPT: { tone: "neutral", icon: DocumentIcon },
  WARRANTY: { tone: "forest", icon: ShieldIcon },
  INVOICE: { tone: "alert", icon: DocumentIcon },
  POLICY: { tone: "forest", icon: ShieldIcon },
};

export function Vault() {
  const store = useClaimBackStore();
  const documents = store.getDocuments();
  const error = store.getError();
  const [selectedDoc, setSelectedDoc] = useState<VaultDocument | null>(null);

  useEffect(() => {
    void store.loadDashboard();
  }, [store]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="font-display text-3xl font-medium text-ink">Document Vault</h1>
        <p className="mt-2 max-w-xl text-ink-soft">
          Every receipt, warranty, and invoice ClaimBack has parsed and matched — the evidence behind every claim.
        </p>
      </div>

      {/* Interactive Upload Dropzone with Live AI OCR simulation & Sample Tester */}
      <UploadDropzone onDocumentReady={(doc) => setSelectedDoc(doc)} />

      {error && (
        <div className="rounded-xl border border-alert/30 bg-alert/10 px-4 py-3 text-sm text-alert">
          {error}
        </div>
      )}

      {/* Documents Table */}
      <div className="overflow-hidden rounded-2xl border border-hairline bg-white/70 shadow-2xs">
        <div className="flex items-center justify-between border-b border-hairline px-4 py-3 bg-cream-100/50">
          <span className="text-xs font-bold uppercase tracking-wider text-ink-faint">
            Stored Documents ({documents.length})
          </span>
          <span className="text-xs text-ink-faint">Click any row to view full PDF & AI extraction</span>
        </div>

        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-hairline bg-cream-100 text-xs uppercase tracking-wide text-ink-faint">
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Document</th>
              <th className="px-4 py-3 font-medium">Issuer / vendor</th>
              <th className="px-4 py-3 font-medium">Uploaded</th>
              <th className="px-4 py-3 text-right font-medium">Confidence</th>
              <th className="px-4 py-3 text-right font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => {
              const meta = docTypeMeta[doc.doc_type] ?? { tone: "neutral" as const, icon: DocumentIcon };
              const Icon = meta.icon;
              return (
                <tr
                  key={doc.doc_id}
                  onClick={() => setSelectedDoc(doc)}
                  className="group cursor-pointer border-b border-hairline last:border-b-0 transition-colors hover:bg-cream-100/70"
                >
                  <td className="px-4 py-3">
                    <Badge tone={meta.tone}>
                      <Icon width={12} height={12} /> {doc.doc_type}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-ink group-hover:text-forest transition-colors">
                      {doc.title}
                    </div>
                    {doc.file_name && (
                      <div className="font-mono text-[11px] text-ink-faint">{doc.file_name}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-ink-soft">{doc.vendor_or_issuer}</td>
                  <td className="px-4 py-3 font-mono text-xs text-ink-faint">{formatDate(doc.uploaded_at)}</td>
                  <td className="px-4 py-3 text-right font-mono text-xs font-semibold text-forest">
                    {Math.round(doc.confidence_score * 100)}%
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDoc(doc);
                      }}
                      className="inline-flex items-center gap-1 rounded-md border border-hairline bg-white px-2 py-1 text-xs font-medium text-ink shadow-2xs transition-colors hover:border-forest hover:text-forest"
                    >
                      <EyeIcon width={13} height={13} />
                      <span>View PDF</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Full Document & PDF Viewer Modal */}
      <DocumentViewerModal document={selectedDoc} onClose={() => setSelectedDoc(null)} />
    </div>
  );
}
