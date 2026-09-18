import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useAuth } from "@/features/auth/hooks/useAuth";

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  tags: TodoTag[];
}

export interface TodoTag {
  id: string;
  name: string;
  color: string | null;
}

export interface TodoFilters {
  status?: boolean;
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

interface TodoListResponse {
  items: Todo[];
  total: number;
  page: number;
  page_size: number;
}

interface CreateTodoRequest {
  title: string;
  description?: string;
}

interface UpdateTodoRequest {
  title?: string;
  description?: string;
  completed?: boolean;
}


export function useTodos(filters: TodoFilters = {}) {
  const { user } = useAuth();
  const params = {
    page: filters.page ?? 1,
    page_size: filters.page_size ?? 20,
    ...(filters.status === undefined ? {} : { status: filters.status }),
    ...(filters.tag_id ? { tag_id: filters.tag_id } : {}),
    ...(filters.keyword ? { keyword: filters.keyword } : {}),
    ...(filters.date_from ? { date_from: filters.date_from } : {}),
    ...(filters.date_to ? { date_to: filters.date_to } : {}),
  };

  return useQuery({
    queryKey: ["todos", user?.id, params],
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", { params });
      return response.data;
    },
    enabled: !!user?.id,
  });
}

export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => {
      const response = await api.post("/todos", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todo created successfully!");
    },
    onError: () => {
      toast.error("Failed to create todo");
    },
  });
}

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async (data: { todo_ids: string[]; completed: boolean }) => {
      const response = await api.patch("/todos/bulk-status", data);
      return response.data as Todo[];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todo status updated");
    },
    onError: () => toast.error("Failed to update todo status"),
  });
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => {
      const response = await api.post(`/todos/${todoId}/tags`, { tag_id: tagId });
      return response.data as TodoTag;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
    onError: () => toast.error("Failed to attach tag"),
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => {
      await api.delete(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
    onError: () => toast.error("Failed to remove tag"),
  });
}

export function useUpdateTodo() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateTodoRequest }): Promise<Todo> => {
      const response = await api.put(`/todos/${id}`, data);
      return response.data;
    },
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches so they don't overwrite the optimistic update
      await queryClient.cancelQueries({ queryKey: ["todos"] });

      // Snapshot ALL cached queries matching the ["todos"] prefix (every page/filter)
      const previousQueries = queryClient.getQueriesData<TodoListResponse>({ queryKey: ["todos"] });

      // Optimistically update every cached page
      queryClient.setQueriesData<TodoListResponse>({ queryKey: ["todos"] }, (old) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((todo) => (todo.id === id ? { ...todo, ...data } : todo)),
        };
      });

      return { previousQueries };
    },
    onError: (_err, _variables, context) => {
      toast.error("Failed to update todo");
      // Roll back each query to its snapshotted state
      context?.previousQueries?.forEach(([queryKey, data]) => {
        queryClient.setQueryData(queryKey, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todo deleted successfully!");
    },
    onError: () => {
      toast.error("Failed to delete todo");
    },
  });
}

export function useToggleTodo() {
  const updateTodo = useUpdateTodo();

  return {
    ...updateTodo,
    mutate: (todo: Todo) => {
      updateTodo.mutate({
        id: todo.id,
        data: { completed: !todo.completed },
      });
    },
  };
}
