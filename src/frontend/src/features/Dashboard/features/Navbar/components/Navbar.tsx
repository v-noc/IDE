import {
  Menubar,
  MenubarMenu,
  MenubarTrigger,
  MenubarContent,
  MenubarItem,
  MenubarSeparator,
  MenubarShortcut,
} from "@/components/ui/menubar";
import { ProgressIndicator } from "./ProgressIndicator";
import HistoryButton from "../../Versioning/components/HistoryButton";
import GitHubStarButton from "@/components/GitHubStarButton";
import { AgentToggleButton } from "../../Agent/components/AgentToggleButton";

interface NavbarProps {
  projectId?: string;
}

const Navbar = ({ projectId }: NavbarProps) => {
  return (
    <div className="w-full flex items-center justify-between">
      <Menubar className="bg-transparent rounded-none shadow-none border-none mx-2 py-1 h-auto">
        <MenubarMenu>
          <MenubarTrigger className="text-xs font-medium rounded-none bg-transparent text-muted-foreground hover:cursor-pointer hover:bg-muted-foreground/10">
            File
          </MenubarTrigger>
          <MenubarContent>
            <MenubarItem>
              New Tab <MenubarShortcut>⌘T</MenubarShortcut>
            </MenubarItem>
            <MenubarItem>New Window</MenubarItem>
            <MenubarSeparator />
            <MenubarItem>Share</MenubarItem>
            <MenubarSeparator />
            <MenubarItem>Print</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger className="text-xs font-medium rounded-none bg-transparent text-muted-foreground hover:cursor-pointer hover:bg-muted-foreground/10">
            Help
          </MenubarTrigger>
          <MenubarContent>
            <MenubarItem>About</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
      </Menubar>
      <div className="flex items-center gap-2 mr-4">
        <ProgressIndicator projectId={projectId} />
        <AgentToggleButton />
        <HistoryButton />
        <GitHubStarButton />
      </div>
    </div>
  );
};

export default Navbar;
