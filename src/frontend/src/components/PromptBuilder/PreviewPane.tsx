import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Check, Copy } from "lucide-react";

interface PreviewPaneProps {
  xml: string;
}

export const PreviewPane: React.FC<PreviewPaneProps> = ({ xml }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(xml);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("Failed to copy:", e);
    }
  };

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <Button
          size="sm"
          variant={copied ? "default" : "secondary"}
          onClick={handleCopy}
          className="gap-2"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              Copy
            </>
          )}
        </Button>
      </div>
      <Textarea
        className="flex-1 font-mono text-xs resize-none"
        value={xml}
        readOnly
      />
    </div>
  );
};

export default PreviewPane;
