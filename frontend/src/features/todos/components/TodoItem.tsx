import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { CheckCircle2, ListChecks, Pencil, Trash2 } from "lucide-react";
import type { Todo, TodoTag } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  selected: boolean;
  onSelect: (id: string, selected: boolean) => void;
}

export function TodoItem({ todo, onToggle, onEdit, onDelete, selected, onSelect }: TodoItemProps) {
  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant={selected ? "default" : "outline"}
        size="icon"
        className="h-8 w-8 shrink-0"
        aria-pressed={selected}
        aria-label={selected ? `Remove ${todo.title} from bulk selection` : `Select ${todo.title} for bulk actions`}
        title={selected ? "Remove from bulk selection" : "Select for bulk actions"}
        onClick={() => onSelect(todo.id, !selected)}
      >
        <ListChecks className="h-3.5 w-3.5" />
      </Button>
      <div className="flex min-w-0 flex-1 items-center gap-3 rounded-lg border bg-card p-3 transition-colors group hover:bg-accent/50">
        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
          aria-label={todo.completed ? `Mark ${todo.title} active` : `Mark ${todo.title} completed`}
        />
        <CheckCircle2 className={`h-4 w-4 shrink-0 ${todo.completed ? "text-emerald-600" : "text-muted-foreground/50"}`} aria-hidden="true" />

        <div className="min-w-0 flex-1">
          <label
            htmlFor={`todo-${todo.id}`}
            className={`cursor-pointer text-sm font-medium ${todo.completed ? "text-muted-foreground line-through" : ""}`}
          >
            {todo.title}
          </label>
          {todo.description && <p className="mt-0.5 truncate text-xs text-muted-foreground">{todo.description}</p>}
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {todo.tags.map((tag: TodoTag) => (
              <span
                key={tag.id}
                className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium"
                style={{
                  color: tag.color || "#64748b",
                  borderColor: tag.color || "#94a3b8",
                  backgroundColor: tag.color ? `color-mix(in srgb, ${tag.color} 14%, transparent)` : "#f1f5f9",
                }}
              >
                {tag.name}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(todo)} title="Edit todo">
            <Pencil className="h-3.5 w-3.5" />
            <span className="sr-only">Edit todo</span>
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => onDelete(todo.id)} title="Delete todo">
            <Trash2 className="h-3.5 w-3.5" />
            <span className="sr-only">Delete todo</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
