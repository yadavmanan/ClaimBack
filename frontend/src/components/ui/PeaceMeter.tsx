import { motion } from "framer-motion";
import { cn } from "../../lib/cn";
import { formatCurrency } from "../../lib/format";

interface PeaceMeterProps {
  openCount: number;
  totalRecoverable: number;
}

export function PeaceMeter({ openCount, totalRecoverable }: PeaceMeterProps) {
  const isCalm = openCount === 0;

  return (
    <div
      className={cn(
        "relative flex items-center gap-5 overflow-hidden rounded-2xl border p-5",
        isCalm ? "border-forest/20 bg-forest-soft" : "border-hairline bg-white/70",
      )}
    >
      <motion.div
        className={cn("h-10 w-10 shrink-0 rounded-full", isCalm ? "bg-forest" : "bg-alert")}
        animate={{ scale: [1, 1.1, 1], opacity: [0.85, 1, 0.85] }}
        transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="min-w-0">
        <p className="font-display text-base italic text-ink-soft">
          {isCalm ? "All quiet." : "Money found."}
        </p>
        <h1 className="mt-0.5 font-display text-2xl font-medium text-ink sm:text-3xl">
          {isCalm
            ? "ClaimBack is watching in the background."
            : `${openCount} opportunit${openCount === 1 ? "y needs" : "ies need"} your review`}
        </h1>
        <p className="mt-2 font-mono text-xs text-ink-soft">
          {isCalm
            ? "No action needed right now."
            : `${formatCurrency(totalRecoverable)} recoverable if approved today`}
        </p>
      </div>
    </div>
  );
}
