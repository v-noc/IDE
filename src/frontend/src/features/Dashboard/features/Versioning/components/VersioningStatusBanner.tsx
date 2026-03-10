import { useVersioningStore } from "../store/useVersioningStore";

function shortCommit(id: string | null): string {
  if (!id) return "";
  return id.slice(0, 8);
}

const VersioningStatusBanner = () => {
  const branch = useVersioningStore((s) => s.branch);
  const headCommitId = useVersioningStore((s) => s.headCommitId);
  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);

  if (!checkedOutCommitId && !compareToCommitId) {
    return null;
  }

  const targetCommitId = checkedOutCommitId ?? headCommitId;

  return (
    <div className="border-b bg-amber-50 px-3 py-2 text-xs text-amber-900">
      {checkedOutCommitId ? (
        <span>
          Checked out commit <strong>{shortCommit(checkedOutCommitId)}</strong> on{" "}
          <strong>{branch}</strong>.
        </span>
      ) : (
        <span>
          Following HEAD on <strong>{branch}</strong>.
        </span>
      )}
      {compareToCommitId && targetCommitId ? (
        <span className="ml-2">
          Comparing <strong>{shortCommit(compareToCommitId)}</strong> with{" "}
          <strong>{shortCommit(targetCommitId)}</strong>.
        </span>
      ) : null}
    </div>
  );
};

export default VersioningStatusBanner;
