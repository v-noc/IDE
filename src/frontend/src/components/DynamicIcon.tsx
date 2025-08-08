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
import type { IconType } from "react-icons";
import * as AiIcons from "react-icons/ai";
import * as BiIcons from "react-icons/bi";
import * as BsIcons from "react-icons/bs";
import * as FaIcons from "react-icons/fa";
import * as FiIcons from "react-icons/fi";
import * as HiIcons from "react-icons/hi2";
import * as IoIcons from "react-icons/io5";
import * as MdIcons from "react-icons/md";
import * as TbIcons from "react-icons/tb";
import { cn } from "@/lib/utils";

interface DynamicIconProps {
  iconName?: string;
  className?: string;
  color?: string;
}

// React-icons registry (same sets as IconSelector)
const allIconSets = {
  ...AiIcons,
  ...BiIcons,
  ...BsIcons,
  ...FaIcons,
  ...FiIcons,
  ...HiIcons,
  ...IoIcons,
  ...MdIcons,
  ...TbIcons,
} as Record<string, IconType>;

// Lucide fallback map
const lucideIconMap: Record<
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
  const ReactIcon = (iconName && allIconSets[iconName]) || undefined;
  const FallbackIcon = lucideIconMap[iconName] || File;

  const IconComponent = ReactIcon || FallbackIcon;

  return (
    <IconComponent
      className={cn(className)}
      style={color ? { color } : undefined}
    />
  );
};
