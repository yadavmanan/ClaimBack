import { animate, useMotionValue, useTransform, motion } from "framer-motion";
import { useEffect } from "react";
import { formatCurrency } from "../../lib/format";

interface StatNumberProps {
  value: number;
  className?: string;
  format?: "currency" | "integer";
}

export function StatNumber({ value, className, format = "currency" }: StatNumberProps) {
  const motionValue = useMotionValue(0);
  const display = useTransform(motionValue, (v) => (format === "currency" ? formatCurrency(v) : Math.round(v).toString()));

  useEffect(() => {
    const controls = animate(motionValue, value, { duration: 0.9, ease: [0.16, 1, 0.3, 1] });
    return controls.stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return <motion.span className={className}>{display}</motion.span>;
}
