import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

// Allow long-running batch executions up to 300s (e.g. for real API runs)
export const maxDuration = 300;

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json();

    const repoRoot = path.resolve(process.cwd(), "..");
    const pythonBin = path.join(repoRoot, ".venv", "bin", "python3");
    const scriptPath = path.join(repoRoot, "tools", "batch_runner.py");

    const proc = spawn(pythonBin, [scriptPath], {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: repoRoot,
      },
    });

    let stdoutData = "";
    let stderrData = "";

    proc.stdin.write(JSON.stringify(payload));
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
        { error: "Batch discovery execution failed", stderr: stderrData },
        { status: 500 }
      );
    }

    try {
      const parsed = JSON.parse(stdoutData);
      return NextResponse.json(parsed);
    } catch (parseErr) {
      return NextResponse.json(
        { error: "Failed to parse batch runner output", raw: stdoutData, stderr: stderrData },
        { status: 500 }
      );
    }
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || "Internal server error" }, { status: 500 });
  }
}
