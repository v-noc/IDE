import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface CodeElementResponse {
  id: string;
  name: string;
  node_type: string;
  qname: string;
  code: string;
  file_path: string;
  file_name: string;
  position: {
    line_no: number;
    col_offset: number;
    end_line_no: number | null;
    end_col_offset: number | null;
  };
}

export const useGetCodeFromElement = (elementId: string) => {
  return useQuery<CodeElementResponse>({
    queryKey: ["codeElement", elementId],
    queryFn: async () => {
      const response = await api(
        `${API_ROUTES.CODE_ELEMENTS}${elementId}/code`
      );
      return response as CodeElementResponse;
    },
    enabled: !!elementId,
  });
};

export interface FileCodeResponse {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  code: string;
}

export const useGetFileCode = (fileId: string) => {
  return useQuery<FileCodeResponse>({
    queryKey: ["fileCode", fileId],
    queryFn: async () => {
      const response = await api(
        `${API_ROUTES.CODE_ELEMENTS}${fileId}/file-code`
      );
      return response as FileCodeResponse;
    },
    enabled: !!fileId,
  });
};
