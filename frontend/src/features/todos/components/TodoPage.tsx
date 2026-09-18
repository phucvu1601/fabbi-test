import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, FilterX, ListFilter, LogOut, Plus, Tags } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { useTags } from "../api/tags";
import { useBulkUpdateStatus, useTodos, type TodoFilters } from "../api/todos";
import { TodoForm } from "./TodoForm";
import { TodoList } from "./TodoList";
import { TagManager } from "./TagManager";

const PAGE_SIZE = 10;

export function TodoPage() {
  const { user, logout } = useAuth();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTagManager, setShowTagManager] = useState(false);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<"all" | "active" | "completed">("all");
  const [tagId, setTagId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const { data: tags = [] } = useTags();
  const bulkUpdate = useBulkUpdateStatus();

  const filters = useMemo<TodoFilters>(() => ({
    page,
    page_size: PAGE_SIZE,
    ...(status === "all" ? {} : { status: status === "completed" }),
    ...(tagId ? { tag_id: tagId } : {}),
    ...(keyword.trim() ? { keyword: keyword.trim() } : {}),
    ...(dateFrom ? { date_from: dateFrom } : {}),
    ...(dateTo ? { date_to: dateTo } : {}),
  }), [page, status, tagId, keyword, dateFrom, dateTo]);
  const { data, isLoading, error } = useTodos(filters);
  const currentPageIds = data?.items.map((todo) => todo.id) ?? [];
  const allCurrentPageSelected = currentPageIds.length > 0 && currentPageIds.every((id) => selectedIds.has(id));
  const hasFilters = Boolean(keyword || tagId || dateFrom || dateTo || status !== "all");
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  const updateSelection = (id: string, selected: boolean) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (selected) next.add(id); else next.delete(id);
      return next;
    });
  };

  const selectCurrentPage = (selected: boolean) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      currentPageIds.forEach((id) => selected ? next.add(id) : next.delete(id));
      return next;
    });
  };

  const clearFilters = () => {
    setKeyword("");
    setStatus("all");
    setTagId("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  const runBulkUpdate = (completed: boolean) => {
    if (!selectedIds.size) return;
    bulkUpdate.mutate({ todo_ids: [...selectedIds], completed }, {
      onSuccess: () => setSelectedIds(new Set()),
    });
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,oklch(0.97_0.04_75),transparent_38%),oklch(0.97_0.98_90)]">
      <header className="border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-5 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">Daily desk</p>
            <h1 className="text-2xl font-semibold tracking-tight">Your todos</h1>
            {user && <p className="text-sm text-muted-foreground">{user.email}</p>}
          </div>
          <Button variant="ghost" size="sm" onClick={logout} title="Log out"><LogOut className="mr-2 h-4 w-4" />Log out</Button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-5 px-4 py-8 sm:px-6">
        <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-medium text-amber-700">Focus queue</p>
            <h2 className="mt-1 text-3xl font-semibold tracking-tight">Make room for what matters.</h2>
            <p className="mt-2 max-w-xl text-sm text-muted-foreground">Filter, group and finish your work without losing the small details.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowTagManager(true)}><Tags className="mr-2 h-4 w-4" />Manage tags</Button>
            <Button onClick={() => setShowCreateForm(true)}><Plus className="mr-2 h-4 w-4" />Add todo</Button>
          </div>
        </section>

        <Card className="border-amber-200/70 shadow-sm">
          <CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base"><ListFilter className="h-4 w-4 text-amber-700" />Filter todos</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Input className="lg:col-span-2" value={keyword} onChange={(event) => { setKeyword(event.target.value); setPage(1); }} placeholder="Search title or description" aria-label="Search todos" />
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={status} onChange={(event) => { setStatus(event.target.value as typeof status); setPage(1); }} aria-label="Filter by status"><option value="all">All statuses</option><option value="active">Active</option><option value="completed">Completed</option></select>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={tagId} onChange={(event) => { setTagId(event.target.value); setPage(1); }} aria-label="Filter by tag"><option value="">All tags</option>{tags.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}</select>
            <Input type="date" value={dateFrom} onChange={(event) => { setDateFrom(event.target.value); setPage(1); }} aria-label="Date from" />
            <Input type="date" value={dateTo} onChange={(event) => { setDateTo(event.target.value); setPage(1); }} aria-label="Date to" />
            {hasFilters && <Button variant="ghost" className="justify-start lg:col-span-6" onClick={clearFilters}><FilterX className="mr-2 h-4 w-4" />Clear filters</Button>}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="flex flex-col gap-3 pb-3 sm:flex-row sm:items-center sm:justify-between">
            <div><CardTitle className="text-lg">My todos</CardTitle><p className="mt-1 text-sm text-muted-foreground">{data?.total ?? 0} items in your queue</p></div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => selectCurrentPage(!allCurrentPageSelected)} disabled={!currentPageIds.length}>{allCurrentPageSelected ? "Clear page" : "Select page"}</Button>
              <Button size="sm" variant="secondary" onClick={() => runBulkUpdate(true)} disabled={!selectedIds.size || bulkUpdate.isPending}>Mark done ({selectedIds.size})</Button>
              <Button size="sm" variant="outline" onClick={() => runBulkUpdate(false)} disabled={!selectedIds.size || bulkUpdate.isPending}>Mark active</Button>
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4">
            {isLoading && <div className="py-12 text-center text-muted-foreground">Loading todos...</div>}
            {error && <div className="py-12 text-center text-destructive">Failed to load todos. Please try again.</div>}
            {data && <TodoList todos={data.items} selectedIds={selectedIds} onSelect={updateSelection} tags={tags} />}
            {data && <div className="mt-5 flex items-center justify-between border-t pt-4 text-sm text-muted-foreground"><span>Page {data.page} of {totalPages}</span><div className="flex gap-1"><Button variant="outline" size="icon" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}><ChevronLeft className="h-4 w-4" /><span className="sr-only">Previous page</span></Button><Button variant="outline" size="icon" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page >= totalPages}><ChevronRight className="h-4 w-4" /><span className="sr-only">Next page</span></Button></div></div>}
          </CardContent>
        </Card>
      </main>

      <TodoForm key="create" mode="create" open={showCreateForm} tags={tags} onClose={() => setShowCreateForm(false)} />
      <TagManager open={showTagManager} onClose={() => setShowTagManager(false)} />
    </div>
  );
}
