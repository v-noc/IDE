import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import * as z from "zod";
import { useForm } from "react-hook-form";
import FileAndFolderSelector from "@/components/FileAndFolderSelector";
import { useCreateProject } from "@/features/Home/hook/useProject";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { parse } from "toml";
import { extractFieldErrors } from "@/utils/errorMessagextractor";
import { idPrefixRemover } from "@/utils";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { CreateProjectPayload } from "@/services/projectService";

/** Backend still requires `path`; clone flow can use this until a real folder is wired. */
const CLONE_PATH_PLACEHOLDER = "/vnoc/__clone_local_path_placeholder__";

type CreateMode = "local" | "remote_new" | "clone";

const formSchema = z
  .object({
    createMode: z.enum(["local", "remote_new", "clone"]),
    path: z.string().min(1, "Path is required"),
    name: z.string().min(3, "Name must be at least 3 characters"),
    description: z.string(),
    remoteUrl: z.string(),
    remoteUsername: z.string(),
    remoteKey: z.string(),
    remoteAuthType: z.enum(["http_basic", "token"]),
  })
  .superRefine((data, ctx) => {
    if (data.createMode === "local") return;
    if (!data.remoteUrl.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Remote URL is required",
        path: ["remoteUrl"],
      });
    }
    if (!data.remoteKey.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Credential is required",
        path: ["remoteKey"],
      });
    }
    if (data.remoteAuthType === "http_basic" && !data.remoteUsername.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Username is required for HTTP basic",
        path: ["remoteUsername"],
      });
    }
  });

type FormValues = z.infer<typeof formSchema>;

interface CreateProjectDialogProps {
  trigger?: React.ReactNode;
  title: string;
  description: string;
}

function buildCreatePayload(values: FormValues): CreateProjectPayload {
  const description = values.description ?? "";
  if (values.createMode === "local") {
    return {
      name: values.name,
      description,
      path: values.path.trim(),
    };
  }

  const auth = {
    type: values.remoteAuthType,
    key: values.remoteKey.trim(),
    ...(values.remoteAuthType === "http_basic"
      ? { username: values.remoteUsername.trim() }
      : {}),
  };

  const remote = {
    remote_url: values.remoteUrl.trim(),
    auth,
  };

  if (values.createMode === "remote_new") {
    return {
      name: values.name,
      description,
      path: values.path.trim(),
      remote_mode: "create_remote",
      remote,
    };
  }

  return {
    name: values.name,
    description,
    path: CLONE_PATH_PLACEHOLDER,
    remote_mode: "clone",
    remote,
  };
}

const CreateProjectDialog = ({
  trigger,
  title,
  description: headerDescription,
}: CreateProjectDialogProps) => {
  const { mutate: createProject, isPending } = useCreateProject();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      createMode: "local",
      path: "",
      name: "",
      description: "",
      remoteUrl: "",
      remoteUsername: "",
      remoteKey: "",
      remoteAuthType: "http_basic",
    },
  });

  const createMode = watch("createMode");

  const onSubmit = (data: FormValues) => {
    const payload = buildCreatePayload(data);
    createProject(payload, {
      onSuccess(data) {
        const key = data.id;
        setTimeout(() => navigate(`/project/${idPrefixRemover(key)}`));
      },
      onError: (error) => {
        const fieldErrors = extractFieldErrors(error);
        if (fieldErrors.length === 0) return;
        fieldErrors.forEach((fe) => {
          const f = fe.field as keyof FormValues;
          if (f in data || f === "path" || f === "name") {
            setError(f, { type: "server", message: fe.message });
          }
        });
      },
    });
  };

  const handleFolderSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const firstFile = files[0];
      const folderPath = firstFile.webkitRelativePath.split("/")[0];
      const allFiles: File[] = Array.from(files);
      const fileDetails = allFiles.map((file) => ({
        name: file.name,
        path: file.webkitRelativePath,
      }));
      const tomlFile = fileDetails.find((file) => file.name === "v-noc.toml");
      if (tomlFile) {
        const tomlFileObject = allFiles.find(
          (file) => file.name === "v-noc.toml",
        );
        if (tomlFileObject) {
          const tomlContent = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (ev) => {
              resolve((ev.target?.result as string) ?? "");
            };
            reader.onerror = () => reject(new Error("Failed to read file"));
            reader.readAsText(tomlFileObject);
          });
          try {
            const tomlData = parse(tomlContent) as {
              pwd?: string;
              name?: string;
              description?: string;
            };
            if (tomlData.pwd) setValue("path", tomlData.pwd);
            if (tomlData.name) setValue("name", tomlData.name);
            if (tomlData.description != null) {
              setValue("description", String(tomlData.description));
            }
          } catch {
            /* ignore */
          }
        }
      }
    }
  };

  const onTabChange = (value: string) => {
    const mode = value as CreateMode;
    setValue("createMode", mode);
    if (mode === "clone") {
      setValue("path", CLONE_PATH_PLACEHOLDER);
    } else if (watch("path") === CLONE_PATH_PLACEHOLDER) {
      setValue("path", "");
    }
  };

  const pathPlaceholder =
    createMode === "remote_new"
      ? "/path/to/local/checkout"
      : "/path/to/existing/project";

  const remoteUrlPlaceholder =
    createMode === "clone"
      ? "https://terminus.example.com:6363/admin/my-remote-db"
      : "https://terminus.example.com:6363";

  return (
    <Dialog>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-[540px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{headerDescription}</DialogDescription>
        </DialogHeader>
        <Tabs value={createMode} onValueChange={onTabChange} className="w-full">
          <TabsList className="grid h-auto w-full grid-cols-3 gap-1 p-1">
            <TabsTrigger value="local" className="text-xs sm:text-sm">
              Local folder
            </TabsTrigger>
            <TabsTrigger value="remote_new" className="text-xs sm:text-sm">
              New on remote
            </TabsTrigger>
            <TabsTrigger value="clone" className="text-xs sm:text-sm">
              Clone remote
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-2">
          {createMode === "clone" && (
            <input type="hidden" {...register("path")} />
          )}

          {createMode !== "clone" && (
            <div className="grid gap-2">
              <Label htmlFor="import-path">Project path</Label>
              <div className="flex gap-2">
                <Input
                  id="import-path"
                  placeholder={pathPlaceholder}
                  {...register("path")}
                  className="flex-1"
                />
                <FileAndFolderSelector
                  handleFolderSelect={handleFolderSelect}
                />
              </div>
              {errors.path?.message && (
                <p className="text-xs text-red-500">{errors.path.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {createMode === "local"
                  ? "Browse to select a project folder, or paste an absolute path."
                  : "Local checkout used for graph analysis after the remote database is cloned."}
              </p>
            </div>
          )}

          {createMode === "clone" && (
            <div className="grid gap-2">
              <Label htmlFor="remote-url">Remote clone URL</Label>
              <Input
                id="remote-url"
                placeholder={remoteUrlPlaceholder}
                {...register("remoteUrl")}
              />
              {errors.remoteUrl?.message && (
                <p className="text-xs text-red-500">{errors.remoteUrl.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Full URL including team and database id (Terminus clone source).
              </p>
            </div>
          )}

          {createMode === "remote_new" && (
            <div className="grid gap-2">
              <Label htmlFor="remote-server-url">Remote server URL</Label>
              <Input
                id="remote-server-url"
                placeholder={remoteUrlPlaceholder}
                {...register("remoteUrl")}
              />
              {errors.remoteUrl?.message && (
                <p className="text-xs text-red-500">{errors.remoteUrl.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Base URL only; database name is derived from the project name.
              </p>
            </div>
          )}

          {createMode === "clone" && (
            <div className="grid gap-2">
              <Label htmlFor="clone-path-placeholder">Local project path</Label>
              <Input
                id="clone-path-placeholder"
                readOnly
                disabled
                value={CLONE_PATH_PLACEHOLDER}
                className="bg-muted font-mono text-xs"
              />
              <p className="text-xs text-muted-foreground">
                Placeholder until folder pick is wired; required by the API for
                now.
              </p>
            </div>
          )}

          <div className="grid gap-2">
            <Label htmlFor="import-name">Project name</Label>
            <Input
              id="import-name"
              placeholder="My project"
              {...register("name")}
            />
            {errors.name?.message && (
              <p className="text-xs text-red-500">{errors.name.message}</p>
            )}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="import-description">Description</Label>
            <Textarea
              id="import-description"
              placeholder="Brief description…"
              {...register("description")}
            />
          </div>

          {createMode !== "local" && (
            <Accordion
              type="single"
              collapsible
              defaultValue="remote-auth"
              className="w-full border-t pt-2"
            >
              <AccordionItem value="remote-auth" className="border-none">
                <AccordionTrigger className="py-2 text-sm font-medium hover:no-underline">
                  Remote authentication
                </AccordionTrigger>
                <AccordionContent className="grid gap-3 pb-2">
                  <p className="text-muted-foreground text-xs">
                    Required for remote and clone. Matches Terminus{" "}
                    <code className="text-xs">Authorization-Remote</code>{" "}
                    payloads.
                  </p>
                  <div className="grid gap-2">
                    <Label htmlFor="remote-auth-type">Auth type</Label>
                    <select
                      id="remote-auth-type"
                      className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
                      {...register("remoteAuthType")}
                    >
                      <option value="http_basic">HTTP basic</option>
                      <option value="token">Token</option>
                    </select>
                  </div>
                  {watch("remoteAuthType") === "http_basic" && (
                    <div className="grid gap-2">
                      <Label htmlFor="remote-username">Username</Label>
                      <Input
                        id="remote-username"
                        autoComplete="username"
                        {...register("remoteUsername")}
                        placeholder="Remote user"
                      />
                      {errors.remoteUsername?.message && (
                        <p className="text-xs text-red-500">
                          {errors.remoteUsername.message}
                        </p>
                      )}
                    </div>
                  )}
                  <div className="grid gap-2">
                    <Label htmlFor="remote-key">
                      {watch("remoteAuthType") === "http_basic"
                        ? "Password / API key"
                        : "Token"}
                    </Label>
                    <Input
                      id="remote-key"
                      type="password"
                      autoComplete="current-password"
                      {...register("remoteKey")}
                    />
                    {errors.remoteKey?.message && (
                      <p className="text-xs text-red-500">
                        {errors.remoteKey.message}
                      </p>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline">
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Creating…" : "Create project"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateProjectDialog;
