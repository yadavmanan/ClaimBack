import { client } from "./client";
import type {
  ActionDraft,
  ActivityEntry,
  AgentTraceEvent,
  ClaimOpportunity,
  CoverageRecord,
  EvidenceRequirement,
  VaultDocument,
} from "../types/models";

type Listener = () => void;

class ClaimBackStore {
  private opportunities: ClaimOpportunity[] = [];
  private documents: VaultDocument[] = [];
  private coverages: CoverageRecord[] = [];
  private requirements: EvidenceRequirement[] = [];
  private drafts: ActionDraft[] = [];
  private traces: AgentTraceEvent[] = [];
  private activity: ActivityEntry[] = [];
  private error: string | null = null;
  private isLoading = false;
  private listeners = new Set<Listener>();
  private version = 0;

  subscribe = (listener: Listener) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = () => this.version;

  private emit() {
    this.version += 1;
    for (const listener of this.listeners) listener();
  }

  getOpportunities = () => this.opportunities;
  getOpportunity = (id: string) => this.opportunities.find((o) => o.opportunity_id === id);
  getDocuments = () => this.documents;
  getDocument = (id: string) => this.documents.find((d) => d.doc_id === id);
  getCoverages = () => this.coverages;
  getError = () => this.error;
  getIsLoading = () => this.isLoading;

  loadDashboard = async () => {
    this.isLoading = true;
    this.error = null;
    this.emit();
    try {
      const [opportunities, documents, coverages, activity] = await Promise.all([
        client.getOpportunities(),
        client.getDocuments(),
        client.getCoverages(),
        client.getActivity(),
      ]);
      this.opportunities = opportunities;
      this.documents = documents;
      this.coverages = coverages;
      this.activity = activity;
    } catch (error) {
      this.error = error instanceof Error ? error.message : "Unable to load ClaimBack data";
    } finally {
      this.isLoading = false;
      this.emit();
    }
  };

  loadOpportunityDetails = async (id: string) => {
    this.isLoading = true;
    this.error = null;
    this.emit();
    try {
      const [opportunity, requirements, drafts, traces] = await Promise.all([
        client.getOpportunity(id),
        client.getRequirements(id),
        client.getDrafts(id),
        client.getTraces(id),
      ]);
      this.opportunities = [opportunity, ...this.opportunities.filter((item) => item.opportunity_id !== id)];
      this.requirements = [...this.requirements.filter((item) => item.opportunity_id !== id), ...requirements];
      this.drafts = [...this.drafts.filter((item) => item.opportunity_id !== id), ...drafts];
      this.traces = [...this.traces.filter((item) => item.opportunity_id !== id), ...traces];
    } catch (error) {
      this.error = error instanceof Error ? error.message : "Unable to load opportunity details";
    } finally {
      this.isLoading = false;
      this.emit();
    }
  };

  uploadDocument = async (file: File, docTypeHint = "RECEIPT") => {
    this.isLoading = true;
    this.error = null;
    this.emit();
    try {
      const result = await client.uploadDocument(file, docTypeHint);
      this.documents = [result.document, ...this.documents.filter((doc) => doc.doc_id !== result.document.doc_id)];
      if (result.coverage) {
        this.coverages = [
          result.coverage,
          ...this.coverages.filter((coverage) => coverage.coverage_id !== result.coverage?.coverage_id),
        ];
      }
      if (result.opportunity) {
        this.opportunities = [
          result.opportunity,
          ...this.opportunities.filter((item) => item.opportunity_id !== result.opportunity?.opportunity_id),
        ];
      }
      if (result.drafts.length > 0) {
        this.drafts = [
          ...this.drafts.filter((draft) => !result.drafts.some((newDraft) => newDraft.draft_id === draft.draft_id)),
          ...result.drafts,
        ];
      }
      await this.loadDashboard();
      return result.document;
    } catch (error) {
      this.error = error instanceof Error ? error.message : "Unable to upload document";
      this.emit();
      throw error;
    } finally {
      this.isLoading = false;
      this.emit();
    }
  };

  deleteDocument = (docId: string) => {
    this.documents = this.documents.filter((d) => d.doc_id !== docId);
    this.emit();
  };
  getRequirements = (opportunityId: string) =>
    this.requirements.filter((r) => r.opportunity_id === opportunityId);
  getDraft = (draftId: string) => this.drafts.find((d) => d.draft_id === draftId);
  getDrafts = (opportunityId: string) => this.drafts.filter((d) => d.opportunity_id === opportunityId);
  getTraces = (opportunityId: string) =>
    this.traces
      .filter((t) => t.opportunity_id === opportunityId)
      .sort((a, b) => (a.timestamp < b.timestamp ? -1 : 1));
  getActivity = () => this.activity;

  approveOpportunity = async (id: string) => {
    try {
      await client.approveOpportunity(id);
      await this.loadDashboard();
      await this.loadOpportunityDetails(id);
    } catch (error) {
      this.error = error instanceof Error ? error.message : "Unable to approve opportunity";
      this.emit();
    }
  };

  dismissOpportunity = async (id: string) => {
    try {
      await client.dismissOpportunity(id);
      await this.loadDashboard();
    } catch (error) {
      this.error = error instanceof Error ? error.message : "Unable to dismiss opportunity";
      this.emit();
    }
  };
}

export const store = new ClaimBackStore();
