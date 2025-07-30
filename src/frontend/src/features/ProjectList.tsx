import { useProjects } from '../services/projectService';
import { useAppStore } from '../store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

const ProjectList = () => {
  const { data: projects, error, isLoading } = useProjects();
  const { viewFormat, searchTerm } = useAppStore();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>An error has occurred: {error.message}</div>;

  const filteredProjects = projects?.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (viewFormat === 'list') {
    return (
      <ul className="space-y-2">
        {filteredProjects?.map((project) => (
          <li key={project.key} className="p-4 border rounded-md">
            <p className="font-semibold">{project.name}</p>
            <p className="text-sm text-gray-500">{project.path}</p>
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {filteredProjects?.map((project) => (
        <Card key={project.key}>
          <CardHeader>
            <CardTitle>{project.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">{project.path}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ProjectList;
