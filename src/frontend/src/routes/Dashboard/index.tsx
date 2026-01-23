import Dashboard from "@/pages/Dashboard";
import { SocketProvider } from "@/services/socket";

export const dashboardRoute = {
  index: true,
  path: "/project/:projectId",
  element: <SocketProvider><Dashboard /></SocketProvider>,
};
