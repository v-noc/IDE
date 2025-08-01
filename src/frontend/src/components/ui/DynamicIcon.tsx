import React from "react";
import {
  File,
  Folder,
  FolderOpen,
  Code,
  FileText,
  Package,
  ChevronRight,
  FolderRoot,
  Parentheses as Function,
  Table,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DynamicIconProps {
  iconName?: string;
  className?: string;
  color?: string;
}

// Simple icon mapping - can be extended as needed
const iconMap: Record<
  string,
  React.ComponentType<React.SVGProps<SVGSVGElement>>
> = {
  File,
  Folder,
  FolderOpen,
  Code,
  FileText,
  Package,
  ChevronRight,
  FolderRoot,
  Function,
  Table,
};

export const DynamicIcon: React.FC<DynamicIconProps> = ({
  iconName = "File",
  className,
  color,
}) => {
  const IconComponent = iconMap[iconName] || File;
  console.log(iconName);
  return (
    <IconComponent
      className={cn(className)}
      style={color ? { color } : undefined}
    />
  );
};
