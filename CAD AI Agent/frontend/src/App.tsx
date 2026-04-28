import { AlertTriangle, Download, FileCog, Loader2, Sparkles, UploadCloud } from "lucide-react";
import { useMemo, useState, type ChangeEvent } from "react";
import { analyzeCad, uploadCad } from "./api";
import Viewer3D from "./components/Viewer3D";
import type { AnalysisPayload, Issue, UploadResponse } from "./types";

const severityStyles = {
  critical: "border-red-500/30 bg-red-500/10 text-red-100",
  warning: "border-yellow-400/30 bg-yellow-400/10 text-yellow-100",
  info: "border-blue-400/30 bg-blue-400/10 text-blue-100"
};

export default function App() {
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null);
  const [activeIssue, setActiveIssue] = useState<Issue | null>(null);
  const [busyState, setBusyState] = useState<"idle" | "uploading" | "analyzing">("idle");
  const [error, setError] = useState<string | null>(null);

  const issues = analysis?.analysis.issues ?? [];
  const groupedSummary = useMemo(() => analysis?.analysis.summary, [analysis]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setBusyState("uploading");
      setError(null);
      setAnalysis(null);
      setActiveIssue(null);
      setUploadData(await uploadCad(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusyState("idle");
      event.target.value = "";
    }
  };

  const runValidation = async () => {
    if (!uploadData) return;
    try {
      setBusyState("analyzing");
      setError(null);
      const result = await analyzeCad(uploadData.fileId);
      setAnalysis(result);
      setActiveIssue(result.analysis.issues[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setBusyState("idle");
    }
  };

  return (
    <main className="min-h-screen px-5 py-6 text-slate-50 md:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-7xl flex-col gap-6">
        <section className="rounded-[32px] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-glow/30 bg-glow/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-glow">
                AI-driven design intelligence
              </div>
              <h1 className="font-display text-4xl font-bold text-white md:text-5xl">
                Early-stage CAD validation with geometry rules and manufacturability signals.
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300 md:text-base">
                Upload a STEP or STL model, analyze wall thickness and risky features, inspect flagged regions in 3D, and export a validation report.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex cursor-pointer items-center justify-center gap-3 rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-4 text-sm font-semibold text-white transition hover:border-glow/40 hover:bg-slate-900">
                {busyState === "uploading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
                Upload STEP/STL
                <input type="file" accept=".stl,.step,.stp" className="hidden" onChange={handleFileChange} />
              </label>

              <button
                className="flex items-center justify-center gap-3 rounded-2xl border border-glow/20 bg-glow/90 px-4 py-4 text-sm font-semibold text-slate-950 transition hover:bg-glow disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!uploadData || busyState !== "idle"}
                onClick={runValidation}
              >
                {busyState === "analyzing" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Run AI Validation
              </button>

              <a
                href={analysis?.htmlReportUrl}
                target="_blank"
                rel="noreferrer"
                className={`flex items-center justify-center gap-3 rounded-2xl border px-4 py-4 text-sm font-semibold transition ${
                  analysis ? "border-white/10 bg-white/10 text-white hover:bg-white/15" : "pointer-events-none border-white/5 bg-white/5 text-slate-500"
                }`}
              >
                <FileCog className="h-4 w-4" />
                Generate Report
              </a>

              <a
                href={analysis?.jsonReportUrl}
                target="_blank"
                rel="noreferrer"
                className={`flex items-center justify-center gap-3 rounded-2xl border px-4 py-4 text-sm font-semibold transition ${
                  analysis ? "border-white/10 bg-white/10 text-white hover:bg-white/15" : "pointer-events-none border-white/5 bg-white/5 text-slate-500"
                }`}
              >
                <Download className="h-4 w-4" />
                JSON Report
              </a>
            </div>
          </div>

          {error && <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div>}
        </section>

        <section className="grid flex-1 gap-6 lg:grid-cols-[1.35fr_0.75fr]">
          <div className="min-h-[560px] rounded-[32px] border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
            <Viewer3D previewUrl={uploadData?.previewUrl ?? null} issues={issues} activeIssueId={activeIssue?.id ?? null} />
          </div>

          <aside className="flex flex-col gap-4 rounded-[32px] border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Critical" value={groupedSummary?.critical ?? 0} accent="text-red-300" />
              <StatCard label="Warnings" value={groupedSummary?.warning ?? 0} accent="text-yellow-200" />
              <StatCard label="Info" value={groupedSummary?.info ?? 0} accent="text-blue-200" />
              <StatCard label="Score" value={groupedSummary?.manufacturabilityScore ?? "--"} accent="text-glow" />
            </div>

            <div className="rounded-[24px] border border-white/10 bg-slate-950/50 p-4">
              <h2 className="font-display text-lg font-semibold text-white">Model metadata</h2>
              {uploadData ? (
                <div className="mt-3 space-y-2 text-sm text-slate-300">
                  <div>Name: {uploadData.originalName}</div>
                  <div>Extents: {uploadData.metadata.extentsMm.map((value) => value.toFixed(2)).join(" x ")} mm</div>
                  <div>Faces: {uploadData.metadata.faceCount}</div>
                  <div>Surface area: {uploadData.metadata.areaMm2 ? `${uploadData.metadata.areaMm2.toFixed(2)} mm^2` : "n/a"}</div>
                  <div>Volume: {uploadData.metadata.volumeMm3 ? `${uploadData.metadata.volumeMm3.toFixed(2)} mm^3` : "n/a"}</div>
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-400">Upload a CAD model to inspect geometry metadata.</p>
              )}
            </div>

            <div className="min-h-[320px] rounded-[24px] border border-white/10 bg-slate-950/50 p-4">
              <div className="mb-3 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-glow" />
                <h2 className="font-display text-lg font-semibold text-white">Validation issues</h2>
              </div>

              <div className="space-y-3 overflow-auto pr-1">
                {issues.length === 0 ? (
                  <p className="text-sm text-slate-400">Run validation to see issue severity, locations, and suggested fixes.</p>
                ) : (
                  issues.map((issue) => (
                    <button
                      key={issue.id}
                      type="button"
                      onClick={() => setActiveIssue(issue)}
                      className={`w-full rounded-2xl border p-4 text-left transition ${
                        activeIssue?.id === issue.id ? "border-glow/40 bg-white/10" : `${severityStyles[issue.severity]} hover:bg-white/10`
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-white">{issue.title}</div>
                          <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-300">{issue.type}</div>
                        </div>
                        <div className="rounded-full border border-white/10 px-2 py-1 text-xs font-semibold text-white">
                          {Math.round(issue.confidence * 100)}%
                        </div>
                      </div>
                      <p className="mt-3 text-sm text-slate-200">{issue.description}</p>
                      <p className="mt-3 text-xs text-slate-300">Fix: {issue.suggestedFix}</p>
                    </button>
                  ))
                )}
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{label}</div>
      <div className={`mt-2 font-display text-3xl font-semibold ${accent}`}>{value}</div>
    </div>
  );
}
