import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export type RemoteAuthFormValues = {
  type: string;
  username: string;
  key: string;
};

type RemoteSyncAuthDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "push" | "pull";
  isPending: boolean;
  onConfirm: (auth: RemoteAuthFormValues) => void;
};

const RemoteSyncAuthDialog = ({
  open,
  onOpenChange,
  mode,
  isPending,
  onConfirm,
}: RemoteSyncAuthDialogProps) => {
  const [authType, setAuthType] = React.useState("http_basic");
  const [username, setUsername] = React.useState("");
  const [key, setKey] = React.useState("");

  React.useEffect(() => {
    if (!open) {
      setUsername("");
      setKey("");
      setAuthType("http_basic");
    }
  }, [open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) return;
    if (authType === "http_basic" && !username.trim()) return;
    onConfirm({
      type: authType,
      username: authType === "http_basic" ? username.trim() : "",
      key: key.trim(),
    });
  };

  const title = mode === "push" ? "Push to remote" : "Pull from remote";
  const description =
    mode === "push"
      ? "Terminus uses the configured remote (e.g. origin). Enter credentials for this operation."
      : "Pull updates from the remote. Enter credentials for this operation.";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div className="grid gap-2">
              <Label htmlFor="remote-auth-type">Auth type</Label>
              <select
                id="remote-auth-type"
                className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
                value={authType}
                onChange={(e) => setAuthType(e.target.value)}
              >
                <option value="http_basic">HTTP basic</option>
                <option value="token">Token</option>
              </select>
            </div>
            {authType === "http_basic" && (
              <div className="grid gap-2">
                <Label htmlFor="remote-auth-user">Username</Label>
                <Input
                  id="remote-auth-user"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Remote user"
                />
              </div>
            )}
            <div className="grid gap-2">
              <Label htmlFor="remote-auth-key">
                {authType === "http_basic" ? "Password / API key" : "Token"}
              </Label>
              <Input
                id="remote-auth-key"
                type="password"
                autoComplete="current-password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="••••••••"
              />
            </div>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={
                isPending ||
                !key.trim() ||
                (authType === "http_basic" && !username.trim())
              }
            >
              {isPending ? "Working…" : mode === "push" ? "Push" : "Pull"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default RemoteSyncAuthDialog;
