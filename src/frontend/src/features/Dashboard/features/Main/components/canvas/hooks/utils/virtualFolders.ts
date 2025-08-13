import type { VirtualFolderResponse } from "@/features/Dashboard/service/useProject";
import type { CommonVNode } from "./types";

export function processVirtualFolders(vf: VirtualFolderResponse): CommonVNode {
    const lt = vf.link_to;
    const base: CommonVNode = {
        id: vf.id,
        name: vf.name || lt?.name || "",
        call_order: vf.call_order,
        node_type: (lt?.node_type || vf.node_type) as any,
        root_id: lt?.id || vf.id,
        qname: vf.qname || lt?.qname,
        theme: lt?.theme || vf.theme,
        children: (vf.children || []).map(processVirtualFolders),
    };
    if (lt?.node_type === "class") {
        return { ...base, fields: lt?.fields };
    } else if (lt?.node_type === "function") {
        return { ...base, inputs: lt?.inputs, outputs: lt?.outputs };
    }
    return base;
}


