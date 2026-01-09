import { api } from "@/lib/api";

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  code: string;
}

export const codeApi = {
  getCode: (elementId: string): Promise<CodeData> => api(`/code-elements/${elementId}/code`),
  writeCode: (elementId: string, code: string): Promise<void> => api(`/code-elements/${elementId}/write-code`, {
    method: 'POST',
    body: { code },
  }),
}
