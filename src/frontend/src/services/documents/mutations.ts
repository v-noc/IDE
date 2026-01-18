import { useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi, type CreateDocumentRequest, type UpdateDocumentRequest } from "./api";
import queryKeys from "@/lib/queryKeys";

/**
 * Create document mutation.
 * Automatically invalidates the cache so all consumers update.
 */
export const useCreateDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateDocumentRequest) =>
      documentsApi.createDocument(payload),
    onSuccess: (_, { node_id }) => {
      // Invalidate documents list for the node
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.list(node_id) });
    },
  });
};

/**
 * Update document mutation.
 * Updates cache directly without invalidating/refetching to prevent cursor glitches.
 */
export const useUpdateDocument = (nodeId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateDocumentRequest) =>
      documentsApi.updateDocument(payload),
    onSuccess: (updatedDocument, variables) => {
      // Update the cache directly without invalidating/refetching
      // This prevents cursor glitches and keeps UI in sync between main view and right sidebar
      queryClient.setQueryData<typeof updatedDocument[]>(
        queryKeys.documents.list(nodeId),
        (oldData) => {
          if (!oldData) return oldData;

          let hasChanges = false;
          const updatedDocs = oldData.map((doc) => {
            if (doc._key !== updatedDocument._key) {
              return doc; // Return same reference for unchanged docs
            }

            // Use updated_at timestamp to determine if document was actually updated
            // Only update if server's updated_at is newer than cache's updated_at
            const serverUpdatedAt = new Date(updatedDocument.updated_at).getTime();
            const cacheUpdatedAt = new Date(doc.updated_at).getTime();

            // If server timestamp is not newer, don't update (prevents unnecessary re-renders)
            if (serverUpdatedAt <= cacheUpdatedAt) {
              return doc; // Return same reference - prevents unnecessary re-renders
            }

            hasChanges = true;
            return {
              ...doc,
              // Update fields from server response (source of truth)
              // Only update fields that were provided in the mutation
              ...(variables.data !== undefined && { data: updatedDocument.data }),
              ...(variables.name !== undefined && { name: updatedDocument.name }),
              ...(variables.description !== undefined && {
                description: updatedDocument.description,
              }),
              // Always update timestamp from server response
              updated_at: updatedDocument.updated_at,
            };
          });

          // Return same array reference if nothing changed
          return hasChanges ? updatedDocs : oldData;
        }
      );
    },
  });
};

/**
 * Delete document mutation.
 * Automatically invalidates the cache so all consumers update.
 */
export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ documentId, nodeId }: { documentId: string; nodeId: string }) =>
      documentsApi.deleteDocument(documentId, nodeId),
    onSuccess: (_, { nodeId }) => {
      // Invalidate documents list for the node
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.list(nodeId) });
    },
  });
};

