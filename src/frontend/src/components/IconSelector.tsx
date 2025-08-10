import React from "react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
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
import { useVirtualizer } from "@tanstack/react-virtual";

export type IconSelectorProps = {
  value?: string;
  onChange: (iconName: string) => void;
  placeholder?: string;
  className?: string;
};

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
};

const ICON_OPTIONS: { name: string; Icon: IconType }[] = Object.entries(
  allIconSets
)
  .filter(
    ([, IconComponent]) =>
      typeof IconComponent === "function" && IconComponent.name
  )
  .map(([name, Icon]) => ({ name, Icon }));

const getIconByName = (name?: string): IconType | null => {
  if (!name) return null;
  return (allIconSets[name as keyof typeof allIconSets] as IconType) || null;
};

const IconSelector: React.FC<IconSelectorProps> = ({
  value,
  onChange,
  placeholder = "Select icon...",
  className,
}) => {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const deferredSearch = React.useDeferredValue(search);

  const filteredIcons = React.useMemo(() => {
    if (!deferredSearch) return ICON_OPTIONS;
    return ICON_OPTIONS.filter((icon) =>
      icon.name.toLowerCase().includes(deferredSearch.toLowerCase())
    );
  }, [deferredSearch]);

  const SelectedIcon = React.useMemo(() => getIconByName(value), [value]);

  const parentRef = React.useRef(null);

  const virtualizer = useVirtualizer({
    count: filteredIcons.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,
    overscan: 20,
  });

  React.useEffect(() => {
    if (open) {
      // Very naive, but it works.
      setTimeout(() => {
        virtualizer.measure();
      }, 100);
    }
  }, [open, virtualizer]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className={className}
          aria-label="Select icon"
        >
          {SelectedIcon ? <SelectedIcon /> : null}
          {value || placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="p-0 w-64">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search icons..."
            value={search}
            onValueChange={setSearch}
          />
          <CommandList ref={parentRef}>
            {filteredIcons.length === 0 ? (
              <CommandEmpty>No icons found.</CommandEmpty>
            ) : (
              <CommandGroup
                style={{
                  height: `${virtualizer.getTotalSize()}px`,
                  width: "100%",
                  position: "relative",
                }}
              >
                {virtualizer.getVirtualItems().map((virtualItem) => {
                  const { name, Icon } = filteredIcons[virtualItem.index];
                  return (
                    <CommandItem
                      key={name}
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: `${virtualItem.size}px`,
                        transform: `translateY(${virtualItem.start}px)`,
                      }}
                      onSelect={() => {
                        onChange(name);
                        setOpen(false);
                      }}
                    >
                      <Icon />
                      <span className="truncate">{name}</span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};

export default IconSelector;
