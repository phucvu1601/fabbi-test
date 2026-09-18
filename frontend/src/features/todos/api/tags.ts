import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useAuth } from "@/features/auth/hooks/useAuth";

export interface Tag {
  id: string;
  user_id: string;
  name: string;
  color: string | null;
  created_at: string;
  updated_at: string;
}

export interface TagInput {
  name: string;
  color?: string;
}

const tagsKey = (userId?: string) => ["tags", userId];

export function useTags() {
  const { user } = useAuth();
  return useQuery({
    queryKey: tagsKey(user?.id),
    queryFn: async (): Promise<Tag[]> => (await api.get("/tags")).data,
    enabled: !!user?.id,
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: TagInput): Promise<Tag> => (await api.post("/tags", data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag created");
    },
    onError: () => toast.error("Tag name already exists"),
  });
}

export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TagInput }): Promise<Tag> =>
      (await api.patch(`/tags/${id}`, data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag updated");
    },
    onError: () => toast.error("Tag name already exists"),
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag deleted");
    },
    onError: () => toast.error("Failed to delete tag"),
  });
}