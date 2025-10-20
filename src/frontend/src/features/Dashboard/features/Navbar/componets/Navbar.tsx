import { useState } from "react";
import BranchSelector from "./BranchSelector";
import CompareModal from "./CompareModal";
import { GitCompare } from "lucide-react";

const Navbar = () => {
  const [isCompareOpen, setCompareOpen] = useState(false);

  return (
    <div className="w-full flex items-center justify-between">
      <div className="flex items-center gap-3">
        <BranchSelector />
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="text-xs inline-flex items-center gap-1 px-2 py-1 rounded border hover:bg-accent"
          onClick={() => setCompareOpen(true)}
        >
          <GitCompare className="h-4 w-4" /> Compare
        </button>
      </div>
      <CompareModal
        isOpen={isCompareOpen}
        onClose={() => setCompareOpen(false)}
      />
    </div>
  );
};

export default Navbar;
