import type {
  ActionDraft,
  ActivityEntry,
  AgentTraceEvent,
  ClaimOpportunity,
  CoverageRecord,
  EvidenceRequirement,
  VaultDocument,
} from "../types/models";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const DEFAULT_USER_ID = import.meta.env.VITE_CLAIMBACK_USER_ID ?? "usr_demo";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : `Request failed with ${response.status}`;
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const client = {
  getOpportunities: (userId = DEFAULT_USER_ID) =>
    request<{ opportunities: ClaimOpportunity[] }>(`/api/users/${userId}/opportunities`).then((body) => body.opportunities),
  getOpportunity: (id: string) =>
    request<{ opportunity: ClaimOpportunity }>(`/api/opportunities/${id}`).then((body) => body.opportunity),
  getDocuments: (userId = DEFAULT_USER_ID) =>
    request<{ documents: VaultDocument[] }>(`/api/users/${userId}/documents`).then((body) => body.documents),
  getCoverages: (userId = DEFAULT_USER_ID) =>
    request<{ coverages: CoverageRecord[] }>(`/api/users/${userId}/coverages`).then((body) => body.coverages),
  getRequirements: (opportunityId: string) =>
    request<{ requirements: EvidenceRequirement[] }>(`/api/opportunities/${opportunityId}/requirements`).then(
      (body) => body.requirements,
    ),
  getDrafts: (opportunityId: string) =>
    request<{ drafts: ActionDraft[] }>(`/api/opportunities/${opportunityId}/drafts`).then((body) => body.drafts),
  getTraces: (opportunityId: string) =>
    request<{ traces: AgentTraceEvent[] }>(`/api/opportunities/${opportunityId}/traces`).then((body) => body.traces),
  getActivity: (userId = DEFAULT_USER_ID) =>
    request<{ activity: ActivityEntry[] }>(`/api/users/${userId}/activity`).then((body) => body.activity),
  uploadDocument: (file: File, docTypeHint = "RECEIPT", userId = DEFAULT_USER_ID) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type_hint", docTypeHint);
    return request<{
      document: VaultDocument;
      coverage: CoverageRecord | null;
      opportunity: ClaimOpportunity | null;
      drafts: ActionDraft[];
    }>(`/api/users/${userId}/documents/upload`, {
      method: "POST",
      body: formData,
    });
  },
  approveOpportunity: async (id: string, userId = DEFAULT_USER_ID) => {
    await request(`/api/opportunities/${id}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, decision: "APPROVE" }),
    });
    return request(`/api/opportunities/${id}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  },
  dismissOpportunity: (id: string, userId = DEFAULT_USER_ID) =>
    request(`/api/opportunities/${id}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, decision: "DISMISSED" }),
    }),
};
