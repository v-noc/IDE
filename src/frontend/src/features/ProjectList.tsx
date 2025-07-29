import { useProjects } from '../services/projectService';
import { useAppStore } from '../store/appStore';

const ProjectList = () => {
  const { data, error, isLoading } = useProjects();
  const { count, increment } = useAppStore();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>An error has occurred: {error.message}</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold">Projects</h2>
      <ul>
        {data?.map((project: any) => (
          <li key={project.key}>{project.name}</li>
        ))}
      </ul>
      <div className="mt-4">
        <p>Zustand count: {count}</p>
        <button 
          onClick={increment} 
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Increment
        </button>
      </div>
    </div>
  );
};

export default ProjectList;
