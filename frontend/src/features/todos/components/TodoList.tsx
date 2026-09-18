import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";
import type { Tag } from "../api/tags";

interface TodoListProps {
  todos: Todo[];
  selectedIds: Set<string>;
  onSelect: (id: string, selected: boolean) => void;
  tags: Tag[];
}

export function TodoList({ todos, selectedIds, onSelect, tags }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos yet</p>
        <p className="text-sm mt-1">Create your first todo to get started</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
            selected={selectedIds.has(todo.id)}
            onSelect={onSelect}
          />
        ))}
      </div>

      {editingTodo && (
        <TodoForm
          key={editingTodo.id}
          mode="edit"
          todo={editingTodo}
          open={!!editingTodo}
          tags={tags}
          onClose={() => setEditingTodo(null)}
        />
      )}
    </>
  );
}
