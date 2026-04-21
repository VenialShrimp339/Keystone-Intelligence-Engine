import ReactMarkdown from "react-markdown";

interface MarkdownResultProps {
  markdown: string | null;
}

export function MarkdownResult({ markdown }: MarkdownResultProps) {
  if (!markdown) {
    return (
      <section className="px-5 py-8">
        <div className="rounded-md border bg-white p-6 text-sm text-muted-foreground shadow-panel">
          No final brief yet.
        </div>
      </section>
    );
  }

  return (
    <section className="px-5 py-5">
      <div className="rounded-md border bg-white p-6 shadow-panel">
        <div className="markdown-body">
          <ReactMarkdown>{markdown}</ReactMarkdown>
        </div>
      </div>
    </section>
  );
}
