import { useSyncExternalStore } from "react";
import { store } from "../api/store";

/** Reactive read access to the in-memory store; re-renders when it changes. */
export function useClaimBackStore() {
  useSyncExternalStore(store.subscribe, store.getVersion);
  return store;
}
