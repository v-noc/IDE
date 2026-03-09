import { versioningApi } from "@/services/versioning";
import type { DiffResult } from "../types/diff";
import { parseVersioningDiff } from "../utils/parseVersioningDiff";

export interface FetchParsedDiffInput {
  projectId: string;
  beforeCommitId: string;
  afterCommitId: string;
}

class VersioningDiffService {
  async fetchParsedDiff(input: FetchParsedDiffInput): Promise<DiffResult> {
    const rawDiff = await versioningApi.getDiff(
      input.projectId,
      input.afterCommitId,
      input.beforeCommitId
    );
    return parseVersioningDiff(rawDiff, input.beforeCommitId, input.afterCommitId);
  }
}

export const versioningDiffService = new VersioningDiffService();

