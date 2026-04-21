import { Github, Star } from "lucide-react";
import { useGitHubStars } from "@/hooks/useGitHubStars";
import { cn } from "@/lib/utils";

interface GitHubStarButtonProps {
  className?: string;
}

const GitHubStarButton = ({ className }: GitHubStarButtonProps) => {
  const { stars } = useGitHubStars();

  return (
    <a
      href="https://github.com/v-noc/IDE"
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "flex items-center gap-1 bg-transparent hover:bg-[#1a1a1a] text-white px-3 py-1 rounded-sm transition-colors border border-white/10 group",
        className,
      )}
    >
      <Github className="h-4 w-4" />

      <div className="flex items-center gap-1 ">
        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
        <div className="bg-[#2a2a2a] px-1 py-0.5 rounded text-xs font-semibold min-w-[30px] text-center">
          {stars !== null ? stars : "..."}
        </div>
      </div>
    </a>
  );
};

export default GitHubStarButton;
