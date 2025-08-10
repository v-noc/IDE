import React from "react";

export type RightSidebarProps = {
  children?: React.ReactNode;
  className?: string;
};

const RightSidebar: React.FC<RightSidebarProps> = ({ children, className }) => {
  return (
    <aside className={`h-full w-full bg-white border-l ${className ?? ""}`}>
      <div className="h-full overflow-auto">
        {children ?? <div>Right sidebar placeholder</div>}
      </div>
    </aside>
  );
};

export default RightSidebar;
