import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface RunCodeRequest {
  code: string;
  path: string;
  executable_path?: string | null;
  examples_path?: string | null;
  command_prefix?: string | null;
  filename?: string | null;
}

export interface RunCodeResponse {
  response: string;
  has_error: boolean;
}

export function useRunCode() {
  return useMutation<RunCodeResponse, Error, RunCodeRequest>({
    mutationFn: async (payload: RunCodeRequest) => {
      return api<RunCodeResponse>(`${API_ROUTES.CODE_ELEMENTS}run-code`, {
        method: "POST",
        body: payload,
      });
    },
  });
}

export default function usePlayGround() {}
