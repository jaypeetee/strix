import { useState } from "react";
import { Download, AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react";
import { fetchRunSummary } from "@/data/serverSource";

interface MarkdownExportViewProps {
  activeRun: string | null;
  onExit: () => void;
}

export default function MarkdownExportView({
  activeRun,
  onExit,
}: MarkdownExportViewProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleExport = async () => {
    if (!activeRun) {
      setError("No active run selected");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch report markdown
      const runSummary = await fetchRunSummary(activeRun);
      if (!runSummary || !runSummary.markdown) {
        setError("Report not available yet. Wait for the scan to complete.");
        setLoading(false);
        return;
      }

      const markdown = runSummary.markdown;

      // Generate filename
      const timestamp = new Date().toISOString().split("T")[0];
      const filename = `strix-report-${activeRun}-${timestamp}.md`;

      // Create blob and download
      const blob = new Blob([markdown], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setSuccess(true);
      setTimeout(() => onExit(), 2000);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to export report"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen dark:bg-black dark:text-white bg-gray-50 text-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <button
          onClick={onExit}
          className="flex items-center gap-2 text-sm dark:text-gray-400 text-gray-600 hover:dark:text-gray-200 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        {/* Card */}
        <div className="dark:bg-[#0a0a0a] dark:border-[#222] bg-white border-gray-200 border rounded-lg p-8">
          {success ? (
            <div className="text-center space-y-4">
              <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto" />
              <h1 className="text-2xl font-bold">Export Complete</h1>
              <p className="dark:text-gray-400 text-gray-600">
                Your report has been downloaded as markdown.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold mb-2">Export Report</h1>
                <p className="dark:text-gray-400 text-gray-600">
                  Download your security findings as a markdown file. No cloud
                  upload, no encryption—just your local copy.
                </p>
              </div>

              {error && (
                <div className="flex gap-3 p-4 dark:bg-red-500/10 dark:border-red-500/20 bg-red-50 border-red-200 border rounded">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-red-600 dark:text-red-400">
                      Error
                    </p>
                    <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                      {error}
                    </p>
                  </div>
                </div>
              )}

              <div className="dark:bg-[#1a1a1a] bg-gray-50 rounded p-4 space-y-3">
                <h3 className="font-semibold dark:text-white text-gray-900">
                  What's included:
                </h3>
                <ul className="text-sm dark:text-gray-400 text-gray-600 space-y-2">
                  <li className="flex items-center gap-2">
                    <span className="dark:bg-green-500/20 dark:text-green-400 bg-green-100 text-green-700 rounded px-2 py-1 text-xs">
                      ✓
                    </span>
                    All findings with severity and details
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="dark:bg-green-500/20 dark:text-green-400 bg-green-100 text-green-700 rounded px-2 py-1 text-xs">
                      ✓
                    </span>
                    Remediation guidance
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="dark:bg-green-500/20 dark:text-green-400 bg-green-100 text-green-700 rounded px-2 py-1 text-xs">
                      ✓
                    </span>
                    Executive summary
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="dark:bg-green-500/20 dark:text-green-400 bg-green-100 text-green-700 rounded px-2 py-1 text-xs">
                      ✓
                    </span>
                    Code locations and POC
                  </li>
                </ul>
              </div>

              <button
                onClick={handleExport}
                disabled={loading}
                className="w-full px-4 py-3 bg-white dark:bg-white text-black rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
                    Preparing report...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Export as Markdown
                  </>
                )}
              </button>

              <p className="text-xs dark:text-gray-500 text-gray-500 text-center">
                Report saved to your Downloads folder
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
