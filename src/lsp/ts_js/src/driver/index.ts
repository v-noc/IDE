import { TsJsDriver } from "./tsJsDriver";

let instance: TsJsDriver | null = null;

export function getTsJsDriver(): TsJsDriver {
  if (!instance) instance = new TsJsDriver();
  return instance;
}

export { TsJsDriver } from "./tsJsDriver";
