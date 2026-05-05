export default function ScreeningChatLoading() {
  return (
    <main className="grid gap-6 md:grid-cols-[0.9fr_1.1fr]">
      <section className="panel">
        <div className="mb-4 flex items-center gap-2">
          <div className="h-8 w-8 animate-pulse rounded-lg bg-muted" />
          <div className="h-7 w-32 animate-pulse rounded-lg bg-muted" />
        </div>
        <div className="space-y-3">
          <div className="h-40 shimmer rounded-xl" />
          <div className="h-10 w-24 shimmer rounded-xl" />
        </div>
      </section>
      <section className="panel space-y-3">
        <div className="mb-1 flex items-center gap-2">
          <div className="h-8 w-8 animate-pulse rounded-lg bg-muted" />
          <div className="h-7 w-32 animate-pulse rounded-lg bg-muted" />
        </div>
        <p className="text-sm text-muted-foreground">正在进入对话...</p>
      </section>
    </main>
  );
}
