import type { FunctionNodeProps } from "../../types/node";
import FunctionNode from "../FunctionNode";

const MethodNode: React.FC<
  { data: FunctionNodeProps } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  return <FunctionNode data={data} {...props} />;
};

export default MethodNode;
