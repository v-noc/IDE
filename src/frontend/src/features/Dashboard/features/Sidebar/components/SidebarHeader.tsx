import { memo } from "react";
import { Link } from "react-router-dom";
import { PiShareNetworkFill } from "react-icons/pi";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchInput } from "./SearchInput";

interface SidebarHeaderProps {
    searchQuery: string;
    setSearchQuery: (query: string) => void;
    /** When true, search is replaced by a skeleton (project tree still loading). */
    loading?: boolean;
}

export const SidebarHeader = memo(function SidebarHeader({
    searchQuery,
    setSearchQuery,
    loading = false,
}: SidebarHeaderProps) {
    return (
        <>
            <Link to="/">
                <div className="text-2xl font-bold flex items-center p-4 gap-2 h-[57px] text-foreground">
                    <PiShareNetworkFill className="size-6 fill-primary" />
                    <span>V-NOC</span>
                </div>
            </Link>
            <Separator />

            <div className="px-3 pt-2 pb-2">
                {loading ? (
                    <Skeleton className="h-9 w-full rounded-md" />
                ) : (
                    <SearchInput
                        value={searchQuery}
                        onChange={setSearchQuery}
                        placeholder="Search nodes..."
                    />
                )}
            </div>
        </>
    );
});
