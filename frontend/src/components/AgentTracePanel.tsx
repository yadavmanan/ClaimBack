import { useState } from "react";
import type { AgentTraceEvent } from "../types/models";
import { AgentIcon, ChevronRightIcon } from "./icons";
import { formatDateTime } from "../lib/format";
import { cn } from "../lib/cn";

const agentColor: Record<AgentTraceEvent["agent"], string> = {
  Parser: "bg-sky-100 text-sky-800",
  Matcher: "bg-violet-100 text-violet-800",
  EvidencePlanner: "bg-amber-100 text-amber-800",
  Drafter: "bg-forest-soft text-forest-dim",
  HumanGate: "bg-ink text-cream",
  Auditor: "bg-alert-soft text-alert",
};

function TraceRow({ event }: { event: AgentTraceEvent }) {
  const [open, setOpen] = useState(false);
  const hasRaw = Object.keys(event.raw).length > 0;

  return (
    <li className="relative pl-8">
      <span className="absolute left-0 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-cream-100 text-ink-soft">
        <AgentIcon width={13} height={13} />
      </span>
      <div className="flex flex-wrap items-center gap-2">
        <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold", agentColor[event.agent])}>
          {event.agent}
        </span>
        <span className="font-mono text-[11px] text-ink-faint">{formatDateTime(event.timestamp)}</span>
      </div>
      <p className="mt-1 text-sm font-medium text-ink">{event.summary}</p>
      <p className="mt-0.5 text-sm text-ink-soft">{event.detail}</p>
      {hasRaw && (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-ink-faint hover:text-ink"
        >
          <ChevronRightIcon width={12} height={12} className={cn("transition-transform", open && "rotate-90")} />
          raw payload
        </button>
      )}
      {open && hasRaw && (
        <pre className="mt-2 overflow-x-auto rounded-lg bg-ink px-3 py-2 font-mono text-[11px] text-cream">
          {JSON.stringify(event.raw, null, 2)}
        </pre>
      )}
    </li>
  );
}

export function AgentTracePanel({ events }: { events: AgentTraceEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-ink-faint">No agent activity recorded yet.</p>;
  }
  return (
    <ul className="flex flex-col gap-5 border-l border-hairline pl-2">
      {events.map((event) => (
        <TraceRow key={event.id} event={event} />
      ))}
    </ul>
  );
}
