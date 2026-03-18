import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import EmptyState from "./components/EmptyState";
import ReportCanvas from "./components/ReportCanvas";
import Sidebar from "./components/Sidebar";
import { mockPortfolioRecords } from "./data/mockReport";
import { uploadPortfolioFile } from "./lib/api";
import { buildReport, loadLiveRecords } from "./lib/reportBuilder";
import type {
  ApiStatus,
  PortfolioRecord,
  PortfolioReport,
  UploadHistoryItem,
  UploadLifecycleState,
  UploadSummary
} from "./types/report";

const initialApiStatus: ApiStatus = {
  connected: false,
  message: "Verificando conexão com a API"
};

const SNAPSHOT_REFRESH_DELAY_MS = 350;
const SNAPSHOT_REFRESH_ATTEMPTS = 3;
const SNAPSHOT_REFRESH_BACKOFF_MS = 500;
const MAX_UPLOAD_HISTORY_ITEMS = 5;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function detectFileTypeFromName(filename: string) {
  const suffix = filename.split(".").pop()?.toLowerCase();
  if (suffix === "csv") return "csv";
  if (suffix === "xlsx" || suffix === "xls") return "excel";
  if (suffix === "json") return "json";
  return suffix || "unknown";
}

export default function App() {
  const [clientName, setClientName] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [records, setRecords] = useState<PortfolioRecord[] | null>(null);
  const [report, setReport] = useState<PortfolioReport | null>(null);
  const [uploadName, setUploadName] = useState<string | null>(null);
  const [reportSourceLabel, setReportSourceLabel] = useState("Workspace executivo de análise");
  const [apiStatus, setApiStatus] = useState<ApiStatus>(initialApiStatus);
  const [loadingLiveData, setLoadingLiveData] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<UploadLifecycleState>("idle");
  const [uploadSummary, setUploadSummary] = useState<UploadSummary | null>(null);
  const [uploadHistory, setUploadHistory] = useState<UploadHistoryItem[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function checkHealth() {
      try {
        const response = await fetch("/health");
        if (!response.ok) {
          throw new Error("API indisponível");
        }

        if (isMounted) {
          setApiStatus({
            connected: true,
            message: "API CarteiraConsol conectada"
          });
        }
      } catch {
        if (isMounted) {
          setApiStatus({
            connected: false,
            message: "API offline. Use mock data ou aguarde o backend para upload real."
          });
        }
      }
    }

    void checkHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!records?.length) {
      setReport(null);
      return;
    }

    setReport(
      buildReport(records, {
        clientName,
        diagnosis,
        sourceLabel: reportSourceLabel
      })
    );
  }, [clientName, diagnosis, records, reportSourceLabel]);

  const sourceContext = useMemo(() => {
    if (uploadName) {
      return `Arquivo processado: ${uploadName}`;
    }
    return report?.sourceLabel ?? reportSourceLabel;
  }, [report?.sourceLabel, reportSourceLabel, uploadName]);

  function appendUploadHistory(item: UploadHistoryItem) {
    setUploadHistory((current) => [item, ...current].slice(0, MAX_UPLOAD_HISTORY_ITEMS));
  }

  function buildHistoryItem(summary: UploadSummary, status: "success" | "error", messageOverride?: string): UploadHistoryItem {
    return {
      ...summary,
      id: `${summary.filename}-${summary.processedAt}-${status}`,
      status,
      message: messageOverride ?? summary.message,
      timestamp: summary.processedAt
    };
  }

  function mountPreview(nextRecords: PortfolioRecord[], sourceLabel: string) {
    setRecords(nextRecords);
    setReportSourceLabel(sourceLabel);
    setLastError(null);
  }

  function handleFillMockData() {
    setUploadName(null);
    setUploadState("idle");
    mountPreview(mockPortfolioRecords, "Snapshot demonstrativo com mock data");
  }

  function handleDownloadTemplate() {
    window.open("/templates/modelo-carteira.csv", "_blank", "noopener,noreferrer");
  }

  function handleSelectUpload() {
    fileInputRef.current?.click();
  }

  async function refreshSnapshotAfterUpload() {
    await sleep(SNAPSHOT_REFRESH_DELAY_MS);

    let lastRefreshError: Error | null = null;
    for (let attempt = 1; attempt <= SNAPSHOT_REFRESH_ATTEMPTS; attempt += 1) {
      try {
        const nextRecords = await loadLiveRecords();
        if (!nextRecords.length) {
          throw new Error("O backend respondeu, mas o snapshot ainda não trouxe posições.");
        }
        return nextRecords;
      } catch (error) {
        lastRefreshError = error instanceof Error ? error : new Error("Falha ao atualizar o snapshot.");
        if (attempt < SNAPSHOT_REFRESH_ATTEMPTS) {
          await sleep(SNAPSHOT_REFRESH_BACKOFF_MS * attempt);
        }
      }
    }

    throw lastRefreshError ?? new Error("Falha ao atualizar o snapshot.");
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadState("uploading");
    setLastError(null);
    let latestSummary: UploadSummary | null = null;

    try {
      const uploadResult = await uploadPortfolioFile(file);
      setUploadName(uploadResult.filename);
      latestSummary = {
        filename: uploadResult.filename,
        detectedType: uploadResult.detected_type,
        rowsProcessed: uploadResult.rows_processed,
        rowsSkipped: uploadResult.rows_skipped,
        message: uploadResult.message,
        processedAt: uploadResult.processed_at,
        rawFile: uploadResult.raw_file,
        processedFile: uploadResult.processed_file
      };
      setUploadSummary(latestSummary);
      appendUploadHistory(buildHistoryItem(latestSummary, "success"));

      setUploadState("processing");
      const nextRecords = await refreshSnapshotAfterUpload();
      mountPreview(nextRecords, "Snapshot atualizado após upload no backend");
      setUploadState("success");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Não foi possível enviar a planilha para o backend.";
      setUploadState("error");
      setLastError(message);

      if (!latestSummary) {
        const fallbackSummary: UploadSummary = {
          filename: file.name,
          detectedType: detectFileTypeFromName(file.name),
          rowsProcessed: 0,
          rowsSkipped: 0,
          message,
          processedAt: new Date().toISOString(),
          rawFile: "",
          processedFile: ""
        };
        setUploadSummary(fallbackSummary);
        appendUploadHistory(buildHistoryItem(fallbackSummary, "error", message));
      }
    } finally {
      event.target.value = "";
    }
  }

  async function handleLoadLiveData() {
    setLoadingLiveData(true);
    try {
      const nextRecords = await loadLiveRecords();
      setUploadName(null);
      setUploadState("idle");
      mountPreview(nextRecords, "Snapshot conectado ao backend CarteiraConsol");
    } catch (error) {
      setLastError(error instanceof Error ? error.message : "Não foi possível carregar os dados atuais da plataforma.");
    } finally {
      setLoadingLiveData(false);
    }
  }

  function handleGeneratePdf() {
    if (!report) {
      setLastError("Gere uma prévia antes de exportar o relatório em PDF.");
      return;
    }
    window.print();
  }

  return (
    <div className="min-h-screen px-4 py-4 md:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-[1680px] gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json"
          className="hidden"
          onChange={(event) => void handleUpload(event)}
        />

        <Sidebar
          clientName={clientName}
          diagnosis={diagnosis}
          apiStatus={apiStatus}
          loadingLiveData={loadingLiveData}
          uploadState={uploadState}
          sourceContext={sourceContext}
          uploadSummary={uploadSummary}
          uploadHistory={uploadHistory}
          lastError={lastError}
          onClientNameChange={setClientName}
          onDiagnosisChange={setDiagnosis}
          onFillMockData={handleFillMockData}
          onDownloadTemplate={handleDownloadTemplate}
          onUploadSpreadsheet={handleSelectUpload}
          onGeneratePdf={handleGeneratePdf}
        />

        <main className="min-w-0">
          {!report ? (
            <EmptyState
              apiStatus={apiStatus}
              loadingLiveData={loadingLiveData}
              onLoadLiveData={handleLoadLiveData}
              onFillMockData={handleFillMockData}
              onUploadSpreadsheet={handleSelectUpload}
            />
          ) : (
            <ReportCanvas report={report} />
          )}
        </main>
      </div>
    </div>
  );
}
