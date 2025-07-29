import { useQuery } from '@tanstack/react-query';

// This would typically be a fetch call to your backend
const fetchProjects = async () => {
  const response = await fetch('/api/core/projects/');
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
};

export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });
};
