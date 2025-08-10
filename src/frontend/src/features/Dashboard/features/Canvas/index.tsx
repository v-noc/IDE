import { useParams } from "react-router";

const MainCanvas = () => {
  const { projectId } = useParams();
  return <div>MainCanvas {projectId}</div>;
};

export default MainCanvas;
