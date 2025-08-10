import React from "react";
import SplitRight from "@/features/Dashboard/features/Main/components/sidebar";

const MainWithRightSidebar: React.FC<{
  left: React.ReactNode;
  right: React.ReactNode;
}> = ({ left, right }) => {
  return <SplitRight left={left} right={right} />;
};

export default MainWithRightSidebar;
