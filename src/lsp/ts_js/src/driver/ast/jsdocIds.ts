import { CLASS_SCHEMA, FUNCTION_SCHEMA } from "../constants";

const ID_RE = /ID:\s*(\S+)/;

export function extractIdFromJsDocs(innerText: string): string | undefined {
  const m = innerText.match(ID_RE);
  return m ? m[1] : undefined;
}

export function formatClassId(uuid: string): string {
  return `${CLASS_SCHEMA}/${uuid}`;
}

export function formatFunctionId(uuid: string): string {
  return `${FUNCTION_SCHEMA}/${uuid}`;
}
