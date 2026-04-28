export type Severity = "critical" | "warning" | "info";

export interface Issue {
  id: string;
  type: string;
  severity: Severity;
  title: string;
  description: string;
  suggestedFix: string;
  confidence: number;
  measurement?: number;
  threshold?: number;
  location: {
    point: [number, number, number];
    radius: number;
    normal?: [number, number, number];
  };
}

export interface UploadResponse {
  fileId: string;
  originalName: string;
  previewUrl: string;
  metadata: {
    extentsMm: [number, number, number];
    faceCount: number;
    volumeMm3: number | null;
    areaMm2: number | null;
  };
}

export interface AnalysisPayload extends UploadResponse {
  analysis: {
    generatedAt: string;
    summary: {
      critical: number;
      warning: number;
      info: number;
      manufacturabilityScore: number;
    };
    issues: Issue[];
    aiInsights: Array<{
      zone: string;
      confidence: number;
      risk: string;
      point: [number, number, number];
    }>;
  };
  htmlReportUrl: string;
  jsonReportUrl: string;
}
