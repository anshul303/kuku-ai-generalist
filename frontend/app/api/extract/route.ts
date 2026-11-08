import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { text, provider = "mock", model = "mock", api_key = "", base_url = "" } = body;

    if (!text || typeof text !== "string" || text.trim().length === 0) {
      return NextResponse.json({ error: "Screenplay text is required" }, { status: 400 });
    }

    const repoRoot = path.resolve(process.cwd(), "..");
    const pythonBin = path.join(repoRoot, ".venv", "bin", "python3");
    const scriptPath = path.join(repoRoot, "tools", "extract_single.py");

    const payload = JSON.stringify({
      text,
      provider,
      model,
      api_key,
      base_url,
    });

    const proc = spawn(pythonBin, [scriptPath], {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: repoRoot,
      },
    });

    let stdoutData = "";
    let stderrData = "";

    proc.stdin.write(payload);
    proc.stdin.end();

    const exitCode = await new Promise<number>((resolve, reject) => {
      proc.stdout.on("data", (chunk) => {
        stdoutData += chunk.toString();
      });
      proc.stderr.on("data", (chunk) => {
        stderrData += chunk.toString();
      });
      proc.on("close", (code) => resolve(code ?? 0));
      proc.on("error", (err) => reject(err));
    });

    if (exitCode !== 0) {
      return NextResponse.json(
        { error: "Extraction pipeline failed", stderr: stderrData },
        { status: 500 }
      );
    }

    try {
      const parsed = JSON.parse(stdoutData);
      return NextResponse.json(parsed);
    } catch (parseErr) {
      return NextResponse.json(
        { error: "Failed to parse pipeline output", raw: stdoutData },
        { status: 500 }
      );
    }
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || "Internal server error" }, { status: 500 });
  }
}
