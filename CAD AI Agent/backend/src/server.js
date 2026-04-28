import cors from "cors";
import express from "express";
import fs from "fs";
import multer from "multer";
import path from "path";
import { fileURLToPath } from "url";
import { randomUUID } from "crypto";
import { spawn } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..", "..");
const BACKEND_DIR = path.resolve(__dirname, "..");
const DATA_DIR = path.join(BACKEND_DIR, "data");
const PYTHON = process.env.PYTHON_PATH || "python";
const PORT = Number(process.env.PORT || 4000);

const ensureDir = (dir) => fs.mkdirSync(dir, { recursive: true });

const dirs = {
  uploads: path.join(DATA_DIR, "uploads"),
  previews: path.join(DATA_DIR, "previews"),
  results: path.join(DATA_DIR, "results"),
  reports: path.join(DATA_DIR, "reports"),
};

Object.values(dirs).forEach(ensureDir);

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, dirs.uploads),
  filename: (_req, file, cb) => {
    const fileId = randomUUID();
    cb(null, `${fileId}${path.extname(file.originalname).toLowerCase()}`);
  },
});

const upload = multer({
  storage,
  fileFilter: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if ([".stl"].includes(ext)) {
      cb(null, true);
      return;
    }
    cb(new Error("Only STL files are currently supported"));
  },
});

const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use("/static/previews", express.static(dirs.previews));
app.use("/static/reports", express.static(dirs.reports));

const runPython = (scriptName, args = []) =>
  new Promise((resolve, reject) => {
    const scriptPath = path.join(ROOT_DIR, "cad-engine", scriptName);
    const child = spawn(PYTHON, [scriptPath, ...args], {
      cwd: ROOT_DIR,
      env: process.env,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      reject(new Error(`Failed to start Python process: ${error.message}`));
    });

    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr || stdout || `Python process failed with code ${code}`));
        return;
      }
      try {
        const lines = stdout
          .split(/\r?\n/)
          .map((line) => line.trim())
          .filter(Boolean);
        const jsonLine = lines.at(-1);
        if (!jsonLine) {
          reject(new Error(stderr || "CAD engine returned no JSON output"));
          return;
        }
        resolve(JSON.parse(jsonLine));
      } catch {
        reject(new Error(`Failed to parse CAD engine response: ${stderr || stdout}`));
      }
    });
  });

const manifestPath = (fileId) => path.join(dirs.results, `${fileId}.json`);

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.post("/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      res.status(400).json({ error: "File is required" });
      return;
    }

    const fileId = path.parse(req.file.filename).name;
    const prep = await runPython("prepare_model.py", [
      "--input",
      req.file.path,
      "--preview-dir",
      dirs.previews,
      "--file-id",
      fileId,
    ]);

    const payload = {
      fileId,
      originalName: req.file.originalname,
      uploadedPath: req.file.path,
      previewUrl: `/static/previews/${prep.previewFile}`,
      metadata: prep.metadata,
    };

    fs.writeFileSync(manifestPath(fileId), JSON.stringify(payload, null, 2));
    res.json(payload);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post("/analyze", async (req, res) => {
  try {
    const { fileId } = req.body;
    if (!fileId) {
      res.status(400).json({ error: "fileId is required" });
      return;
    }

    if (!fs.existsSync(manifestPath(fileId))) {
      res.status(404).json({ error: "Uploaded file not found" });
      return;
    }

    const manifest = JSON.parse(fs.readFileSync(manifestPath(fileId), "utf-8"));
    const analysis = await runPython("analyze_model.py", [
      "--input",
      manifest.uploadedPath,
      "--report-dir",
      dirs.reports,
      "--file-id",
      fileId,
      "--original-name",
      manifest.originalName,
    ]);

    const merged = {
      ...manifest,
      analysis,
      htmlReportUrl: `/static/reports/${fileId}.html`,
      jsonReportUrl: `/report?fileId=${fileId}&format=json`,
    };

    fs.writeFileSync(manifestPath(fileId), JSON.stringify(merged, null, 2));
    res.json(merged);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get("/report", (req, res) => {
  const { fileId, format = "json" } = req.query;
  if (!fileId) {
    res.status(400).json({ error: "fileId is required" });
    return;
  }

  if (!fs.existsSync(manifestPath(fileId))) {
    res.status(404).json({ error: "Report not found" });
    return;
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath(fileId), "utf-8"));
  if (!manifest.analysis) {
    res.status(404).json({ error: "Analysis has not been run yet" });
    return;
  }

  if (format === "html") {
    res.sendFile(path.join(dirs.reports, `${fileId}.html`));
    return;
  }

  res.json({
    fileId,
    originalName: manifest.originalName,
    metadata: manifest.metadata,
    analysis: manifest.analysis,
    generatedAt: manifest.analysis.generatedAt,
  });
});

app.use((error, _req, res, _next) => {
  res.status(500).json({ error: error.message || "Unexpected server error" });
});

app.listen(PORT, () => {
  console.log(`CAD AI backend listening on http://localhost:${PORT}`);
});
