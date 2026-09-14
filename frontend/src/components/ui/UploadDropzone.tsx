import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { UploadIcon, CheckIcon, AgentIcon } from "../icons";
import { useClaimBackStore } from "../../hooks/useClaimBackStore";
import type { VaultDocument } from "../../types/models";

interface UploadDropzoneProps {
  onDocumentReady?: (doc: VaultDocument) => void;
}

export function UploadDropzone({ onDocumentReady }: UploadDropzoneProps) {
  const store = useClaimBackStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState("");
  const [progressPercent, setProgressPercent] = useState(0);

  const processFile = async (file: File) => {
    setIsProcessing(true);
    setProgressPercent(15);
    setProcessingStage("Uploading document to ClaimBack Vault...");

    await new Promise((r) => setTimeout(r, 150));
    setProgressPercent(45);
    setProcessingStage(file.type === "application/pdf" ? "Reading PDF and extracting text..." : "Running AWS Textract OCR...");

    await new Promise((r) => setTimeout(r, 150));
    setProgressPercent(80);
    setProcessingStage("Ingesting parsed facts into ClaimBack...");

    try {
      const document = await store.uploadDocument(file, inferDocTypeHint(file.name));
      document.preview_url ||= URL.createObjectURL(file);
      document.file_name ||= file.name;

      setProgressPercent(100);
      setProcessingStage("Cross-referencing vault policies... Ingest complete.");

      await new Promise((r) => setTimeout(r, 300));
      if (onDocumentReady) {
        onDocumentReady(document);
      }
    } finally {
      setIsProcessing(false);
      setProgressPercent(0);
    }
  };

  const inferDocTypeHint = (filename: string) => {
    const lowerName = filename.toLowerCase();
    if (lowerName.includes("warranty")) return "WARRANTY";
    if (lowerName.includes("policy")) return "POLICY";
    if (lowerName.includes("repair") || lowerName.includes("invoice")) return "REPAIR_INVOICE";
    if (lowerName.includes("bill") || lowerName.includes("statement") || lowerName.includes("jio") || lowerName.includes("airfiber")) {
      return "BILLING_STATEMENT";
    }
    return "RECEIPT";
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
      e.target.value = "";
    }
  };

  const handleTestSample = async () => {
    const response = await fetch("/samples/jio_airfiber_bill.pdf");
    const blob = await response.blob();
    const sample = new File([blob], "jio_airfiber_bill.pdf", { type: "application/pdf" });
    void processFile(sample);
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={handleFileChange}
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        className={`group relative flex flex-col items-center justify-center gap-3.5 rounded-2xl border-2 border-dashed px-6 py-9 text-center transition-all duration-200 cursor-pointer ${
          isDragging
            ? "border-forest bg-forest-soft/40 scale-[1.005]"
            : "border-hairline bg-white/50 hover:border-ink/20 hover:bg-cream-100/50"
        }`}
      >
        {isProcessing ? (
          <div className="flex flex-col items-center gap-3 w-full max-w-md animate-in fade-in">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-forest-soft text-forest animate-pulse">
              <AgentIcon width={24} height={24} />
            </div>

            <div className="w-full">
              <div className="flex items-center justify-between text-xs font-semibold text-ink mb-1.5">
                <span>{processingStage}</span>
                <span className="font-mono text-forest">{progressPercent}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-cream-200">
                <div
                  className="h-full bg-forest transition-all duration-300 rounded-full"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
            <p className="text-[11px] font-mono text-ink-faint">
              Strands Multi-Agent Orchestration • Amazon Bedrock
            </p>
          </div>
        ) : (
          <>
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cream-200 text-ink-soft transition-transform duration-200 group-hover:scale-105 group-hover:text-forest">
              <UploadIcon width={22} height={22} />
            </span>

            <div className="space-y-1">
              <p className="text-sm font-semibold text-ink">
                Drag & drop your PDF, receipt, warranty, or invoice here
              </p>
              <p className="text-xs text-ink-faint">
                Supports PDF, PNG, JPG • ClaimBack OCRs it, extracts facts, and opens the preview instantly
              </p>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                className="rounded-lg border border-hairline bg-white px-3 py-1.5 text-xs font-medium text-ink shadow-2xs transition-colors hover:bg-cream-100"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
              >
                Browse Files
              </button>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleTestSample();
                }}
                className="inline-flex items-center gap-1.5 rounded-lg border border-forest/30 bg-forest-soft px-3 py-1.5 text-xs font-semibold text-forest transition-colors hover:bg-forest hover:text-white"
              >
                <CheckIcon width={12} height={12} />
                Try with sample: Jio AirFiber Bill (PDF)
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
