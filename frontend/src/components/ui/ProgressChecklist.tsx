import type { EvidenceRequirement } from "../../types/models";
import { CheckIcon, MissingIcon } from "../icons";
import { cn } from "../../lib/cn";

interface ProgressChecklistProps {
  requirements: EvidenceRequirement[];
}

export function ProgressChecklist({ requirements }: ProgressChecklistProps) {
  return (
    <ul className="flex flex-col gap-2.5">
      {requirements.map((req) => {
        const satisfied = req.status === "SATISFIED";
        return (
          <li key={req.requirement_id} className="flex items-start gap-3 text-sm">
            <span className={cn("mt-0.5 shrink-0", satisfied ? "text-forest" : "text-alert")}>
              {satisfied ? <CheckIcon width={16} height={16} /> : <MissingIcon width={16} height={16} />}
            </span>
            <div>
              <p className={cn(satisfied ? "text-ink" : "text-alert")}>{req.description}</p>
              {!satisfied && req.user_action_needed && (
                <p className="mt-0.5 text-xs text-ink-faint">{req.user_action_needed}</p>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
