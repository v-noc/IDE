export interface PlaygroundOwnerFields {
  owner_function?: string | null;
  owner_class?: string | null;
  owner_file?: string | null;
  owner_folder?: string | null;
}

export interface Playground {
  id: string;
  name: string;
  description: string;
  relative_path: string;
  code: string;
  executable_path?: string | null;
  filename?: string | null;
  owner_function?: string | null;
  owner_class?: string | null;
  owner_file?: string | null;
  owner_folder?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CreatePlaygroundPayload extends PlaygroundOwnerFields {
  name: string;
  description?: string;
  relative_path: string;
  code: string;
  executable_path?: string | null;
  filename?: string | null;
}

export interface UpdatePlaygroundPayload {
  name?: string;
  description?: string;
  relative_path?: string;
  code?: string;
  executable_path?: string | null;
  filename?: string | null;
}

export interface RunPlaygroundCodePayload {
  playground_id: string;
}

export interface RunPlaygroundCodeResponse {
  response: string;
  has_error: boolean;
}
