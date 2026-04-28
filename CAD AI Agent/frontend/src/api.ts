import type { AnalysisPayload, UploadResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || 'https://cad-google.onrender.com';

async function extractError(response: Response, fallback: string): Promise<Error> {
  const text = await response.text();
  if (!text) {
    return new Error(fallback);
  }

  try {
    const parsed = JSON.parse(text) as { error?: string };
    return new Error(parsed.error || fallback);
  } catch {
    return new Error(text || fallback);
  }
}

export async function uploadCad(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
  if (!response.ok) {
    throw await extractError(response, "Upload failed");
  }
  return response.json();
}

export async function analyzeCad(fileId: string): Promise<AnalysisPayload> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fileId })
  });
  if (!response.ok) {
    throw await extractError(response, "Analysis failed");
  }
  return response.json();
}
