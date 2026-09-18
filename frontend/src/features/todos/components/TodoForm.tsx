import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAttachTag, useCreateTodo, useDetachTag, useUpdateTodo } from "../api/todos";
import { todoSchema, type TodoFormData } from "../schemas/todo";
import type { Todo } from "../api/todos";
import type { Tag } from "../api/tags";

interface TodoFormProps {
  mode: "create" | "edit";
  todo?: Todo;
  open: boolean;
  onClose: () => void;
  tags: Tag[];
}

export function TodoForm({ mode, todo, open, onClose, tags }: TodoFormProps) {
  const createTodo = useCreateTodo();
  const updateTodo = useUpdateTodo();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TodoFormData>({
    resolver: zodResolver(todoSchema),
    defaultValues: {
      title: todo?.title || "",
      description: todo?.description || "",
    },
  });

  const onSubmit = async (data: TodoFormData) => {
    if (mode === "create") {
      const createdTodo = await createTodo.mutateAsync(data);
      await Promise.all(selectedTagIds.map((tagId) => attachTag.mutateAsync({ todoId: createdTodo.id, tagId })));
      reset();
      setSelectedTagIds([]);
      onClose();
      return;
    }

    if (todo) {
      await updateTodo.mutateAsync({ id: todo.id, data });
      const currentTagIds = new Set(todo.tags.map((tag) => tag.id));
      const selectedIds = new Set(selectedTagIds);
      await Promise.all(selectedTagIds.filter((tagId) => !currentTagIds.has(tagId)).map((tagId) => attachTag.mutateAsync({ todoId: todo.id, tagId })));
      await Promise.all(todo.tags.filter((tag) => !selectedIds.has(tag.id)).map((tag) => detachTag.mutateAsync({ todoId: todo.id, tagId: tag.id })));
      onClose();
    }
  };

  const isPending = createTodo.isPending || updateTodo.isPending || attachTag.isPending || detachTag.isPending;

  useEffect(() => {
    reset({
      title: todo?.title || "",
      description: todo?.description || "",
    });
  }, [todo, reset]);

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Create Todo" : "Edit Todo"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="What needs to be done?"
              {...register("title")}
            />
            {errors.title && (
              <p className="text-sm text-destructive">
                {errors.title.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Tags</Label>
            {tags.length === 0 ? (
              <p className="text-sm text-muted-foreground">No tags yet. Create one from Manage tags.</p>
            ) : (
              <div className="flex max-h-28 flex-wrap gap-2 overflow-y-auto rounded-md border p-2">
                {tags.map((tag) => {
                  const selected = selectedTagIds.includes(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      aria-pressed={selected}
                      onClick={() => setSelectedTagIds((current) => selected ? current.filter((id) => id !== tag.id) : [...current, tag.id])}
                      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors ${selected ? "bg-accent font-medium" : "bg-background text-muted-foreground"}`}
                      style={{
                        color: tag.color || "#64748b",
                        borderColor: tag.color || "#94a3b8",
                        backgroundColor: selected
                          ? tag.color
                            ? `color-mix(in srgb, ${tag.color} 22%, white)`
                            : "#f1f5f9"
                          : "transparent",
                      }}
                    >
                      {selected && <Check className="h-3 w-3" strokeWidth={3} />}
                      {tag.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Input
              id="description"
              placeholder="Add details..."
              {...register("description")}
            />
            {errors.description && (
              <p className="text-sm text-destructive">
                {errors.description.message}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending
                ? mode === "create"
                  ? "Creating..."
                  : "Saving..."
                : mode === "create"
                ? "Create"
                : "Save"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
