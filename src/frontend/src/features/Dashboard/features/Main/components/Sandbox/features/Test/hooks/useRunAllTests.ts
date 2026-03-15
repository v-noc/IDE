import { useRunTests } from "@/services/tests";

export function useRunAllTests(projectNodeId: string) {
  const runTestsMutation = useRunTests(projectNodeId);

  const runAllTests = () => runTestsMutation.mutateAsync({});

  return {
    runAllTests,
    isRunning: runTestsMutation.isPending,
    error: runTestsMutation.error,
  };
}
