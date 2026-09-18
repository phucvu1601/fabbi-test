import { useState } from "react";
import { Pencil, Plus, Trash2, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useCreateTag, useDeleteTag, useTags, useUpdateTag, type Tag } from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

export function TagManager({ open, onClose }: TagManagerProps) {
  const { data: tags = [], isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: { name: "", color: "" },
  });

  const startEdit = (tag: Tag) => {
    setEditingTag(tag);
    reset({ name: tag.name, color: tag.color ?? "" });
  };

  const cancelEdit = () => {
    setEditingTag(null);
    reset({ name: "", color: "" });
  };

  const onSubmit = (data: TagFormData) => {
    const payload = { name: data.name, color: data.color || undefined };
    if (editingTag) {
      updateTag.mutate({ id: editingTag.id, data: payload }, { onSuccess: cancelEdit });
    } else {
      createTag.mutate(payload, { onSuccess: () => reset({ name: "", color: "" }) });
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Manage tags</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-3 rounded-lg border bg-muted/30 p-3 sm:grid-cols-[1fr_7rem_auto] sm:items-end">
          <div className="space-y-1">
            <Label htmlFor="tag-name">Name</Label>
            <Input id="tag-name" placeholder="e.g. Work" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="tag-color">Color</Label>
            <Input id="tag-color" type="color" className="h-9 p-1" {...register("color")} />
          </div>
          <div className="flex gap-1">
            <Button type="submit" size="icon" title={editingTag ? "Save tag" : "Create tag"} disabled={createTag.isPending || updateTag.isPending}>
              {editingTag ? <Pencil className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              <span className="sr-only">{editingTag ? "Save tag" : "Create tag"}</span>
            </Button>
            {editingTag && <Button type="button" variant="outline" size="icon" onClick={cancelEdit} title="Cancel editing"><X className="h-4 w-4" /><span className="sr-only">Cancel editing</span></Button>}
          </div>
        </form>
        <div className="max-h-64 space-y-2 overflow-y-auto">
          {isLoading && <p className="text-sm text-muted-foreground">Loading tags...</p>}
          {!isLoading && tags.length === 0 && <p className="text-sm text-muted-foreground">No tags yet.</p>}
          {tags.map((tag) => (
            <div key={tag.id} className="flex items-center justify-between rounded-md border px-3 py-2">
              <div className="flex min-w-0 items-center gap-2">
                <span className="h-3 w-3 shrink-0 rounded-full border" style={{ backgroundColor: tag.color || "#94a3b8" }} />
                <span className="truncate text-sm font-medium">{tag.name}</span>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => startEdit(tag)} title={`Edit ${tag.name}`}><Pencil className="h-3.5 w-3.5" /><span className="sr-only">Edit {tag.name}</span></Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => deleteTag.mutate(tag.id)} title={`Delete ${tag.name}`}><Trash2 className="h-3.5 w-3.5" /><span className="sr-only">Delete {tag.name}</span></Button>
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}