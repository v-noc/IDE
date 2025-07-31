import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import { useParams } from "react-router";

import { ResizablePanelGroup } from "@/components/ui/resizable";

const Dashboard = () => {
  const { projectId } = useParams();
  console.log(projectId);
  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={<div>main</div>}
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;
