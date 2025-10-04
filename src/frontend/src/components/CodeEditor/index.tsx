import Editor, { type EditorProps } from "@monaco-editor/react";
import { Skeleton } from "../ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "../ui/alert";
import { cn } from "@/lib/utils";

interface CodeEditorProps extends EditorProps {
  isLoading?: boolean;
  isError?: boolean;
  errorTitle?: string;
  errorMessage?: string;
}

const CodeEditor = ({
  isLoading,
  isError,
  errorTitle = "Failed to load code",
  errorMessage = "Please try again or select a different item.",
  className,
  options,
  ...rest
}: CodeEditorProps) => {
  if (isLoading) {
    return (
      <div className={cn("h-full w-full p-4", className)}>
        <div className="mb-3">
          <Skeleton className="h-5 w-40" />
        </div>
        <div className="space-y-2">
          {Array.from({ length: 12 }).map((_, index) => (
            <Skeleton key={index} className="h-4 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={cn("h-full w-full p-4", className)}>
        <Alert variant="destructive">
          <AlertTitle>{errorTitle}</AlertTitle>
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <Editor
      className={cn("h-full w-full", className)}
      {...rest}
      options={{
        minimap: { enabled: false },
        wordWrap: "on",
        scrollBeyondLastLine: false,
        ...options,
      }}
    />
  );
};

export default CodeEditor;
