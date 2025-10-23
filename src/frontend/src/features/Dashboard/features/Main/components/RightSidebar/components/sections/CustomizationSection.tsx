import React from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import ColorRow from "./shared/ColorRow";
import type { CustomizationData } from "../../hooks/useConfigSidebarForm";

export type CustomizationSectionProps = {
  value: CustomizationData;
  onChange: (data: CustomizationData) => void;
};

const CustomizationSection: React.FC<CustomizationSectionProps> = ({
  value,
  onChange,
}) => {
  const update = (patch: Partial<CustomizationData>) =>
    onChange({ ...value, ...patch });

  return (
    <Accordion
      type="multiple"
      defaultValue={["appearance", "layout"]}
      className="w-full space-y-3 bg-white"
    >
      <AccordionItem value="appearance" className="!border rounded-md">
        <AccordionTrigger className="px-3 py-2 text-sm font-medium">
          Appearance
        </AccordionTrigger>
        <AccordionContent className="space-y-3 p-3 bg-muted/20">
          <ColorRow
            label="Icon color"
            value={value.iconColor}
            onChange={(v) => update({ iconColor: v })}
          />

          <ColorRow
            label="Text color"
            value={value.textColor ?? "#000000"}
            onChange={(v) => update({ textColor: v })}
          />
          <ColorRow
            label="Card color"
            value={value.cardColor}
            onChange={(v) => update({ cardColor: v })}
          />
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="layout" className="!border rounded-md bg-white">
        <AccordionTrigger className="px-3 py-2 text-sm font-medium">
          Layout
        </AccordionTrigger>
        <AccordionContent className="space-y-3 p-3 ">
          <ColorRow
            label="Navbar color"
            value={value.navbarColor ?? "#f9f9f9"}
            onChange={(v) => update({ navbarColor: v })}
          />
          <ColorRow
            label="Background color"
            value={value.backgroundColor ?? "#f9f9f9"}
            onChange={(v) => update({ backgroundColor: v })}
          />
          <ColorRow
            label="Left sidebar color"
            value={value.leftSidebarColor ?? "#f9f9f9"}
            onChange={(v) => update({ leftSidebarColor: v })}
          />
          <ColorRow
            label="Right sidebar color"
            value={value.rightSidebarColor ?? "#f9f9f9"}
            onChange={(v) => update({ rightSidebarColor: v })}
          />
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};

export default CustomizationSection;
