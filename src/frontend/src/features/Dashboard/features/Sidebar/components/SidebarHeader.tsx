import { memo } from "react";
import { Link } from "react-router-dom";
import { PiShareNetworkFill } from "react-icons/pi";
import { Separator } from "@/components/ui/separator";
import { SearchInput } from "./SearchInput";

interface SidebarHeaderProps {
    searchQuery: string;
    setSearchQuery: (query: string) => void;
}

export const SidebarHeader = memo(function SidebarHeader({
    searchQuery,
    setSearchQuery,
}: SidebarHeaderProps) {
    return (
        <>
            <Link to="/">
                <div className="text-2xl font-bold flex items-center p-4 gap-2 h-[57px] text-white">
                    <PiShareNetworkFill className="size-6 fill-green-600" />
                    <span className="text-black">V-NOC</span>
                </div>
            </Link>
            <Separator />

            <div className="px-3 pt-2">
                <SearchInput
                    value={searchQuery}
                    onChange={setSearchQuery}
                    placeholder="Search nodes..."
                />
            </div>
        </>
    );
});
