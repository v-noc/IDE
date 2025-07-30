import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, List, Grid } from "lucide-react";
import { useState } from "react";

const SearchAndViewController = ({
  viewMode,
  setViewMode,
}: {
  viewMode: "list" | "grid";
  setViewMode: (viewMode: "list" | "grid") => void;
}) => {
  const [searchTerm, setSearchTerm] = useState("");

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="relative w-96">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant={viewMode === "list" ? "default" : "outline"}
          size="sm"
          onClick={() => setViewMode("list")}
        >
          <List className="h-4 w-4" />
        </Button>
        <Button
          variant={viewMode === "grid" ? "default" : "outline"}
          size="sm"
          onClick={() => setViewMode("grid")}
        >
          <Grid className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default SearchAndViewController;
