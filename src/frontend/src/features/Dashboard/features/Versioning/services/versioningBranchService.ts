import type { Branch } from "@/services/versioning";

export interface VersioningBranch {
  id: string;
  name: string;
  isCurrent: boolean;
  headCommit: string;
}

class VersioningBranchService {
  normalizeBranch(branch: Branch): VersioningBranch {
    return {
      id: branch.id,
      name: branch.name,
      isCurrent: branch.is_current,
      headCommit: branch.head_commit,
    };
  }
}

export const versioningBranchService = new VersioningBranchService();
