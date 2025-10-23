import React from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import IconSelector from "@/components/IconSelector";
import type { BasicInfoData } from "../../hooks/useConfigSidebarForm";

export type BasicInfoSectionProps = {
  value: BasicInfoData;
  onChange: (data: BasicInfoData) => void;
};

const FieldLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <label className="text-[11px] uppercase tracking-wide text-muted-foreground font-medium">
    {children}
  </label>
);

const BasicInfoSection: React.FC<BasicInfoSectionProps> = ({
  value,
  onChange,
}) => {
  return (
    <Accordion
      type="single"
      collapsible
      defaultValue="basic"
      className="w-full bg-white"
    >
      <AccordionItem value="basic" className="!border rounded-md">
        <AccordionTrigger className="px-3 py-2 text-sm font-medium">
          Basic Info
        </AccordionTrigger>
        <AccordionContent className="space-y-4 p-4 bg-muted/20">
          <div className="space-y-2">
            <FieldLabel>Name</FieldLabel>
            <Input
              value={value.name}
              onChange={(e) => onChange({ ...value, name: e.target.value })}
              placeholder="Enter name"
              className="h-9"
            />
          </div>
          <div className="space-y-2">
            <FieldLabel>Description</FieldLabel>
            <Textarea
              value={value.description}
              onChange={(e) =>
                onChange({ ...value, description: e.target.value })
              }
              placeholder="Enter description"
              rows={5}
            />
          </div>
          <div className="space-y-2">
            <FieldLabel>Icon</FieldLabel>
            <IconSelector
              value={value.icon}
              onChange={(icon) => onChange({ ...value, icon })}
              className="w-full justify-start"
              placeholder="Select icon..."
            />
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};

export default BasicInfoSection;
