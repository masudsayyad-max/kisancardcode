import { NextRequest, NextResponse } from "next/server";
import { createWriteStream, mkdirSync } from "fs";
import path from "path";
import { verifyToken } from "@/lib/jwt";

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const me = verifyToken(token);
  if (!me) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const data = await req.formData();
  const file = data.get("photo") as unknown as File;
  if (!file) return NextResponse.json({ error: "No file" }, { status: 400 });
  const bytes = Buffer.from(await file.arrayBuffer());
  const photosDir = path.join(process.cwd(), "public", "photos");
  mkdirSync(photosDir, { recursive: true });
  const filename = `user_${me.id}_${Date.now()}_${file.name}`.replace(/[^\w.\-]/g, "_");
  const full = path.join(photosDir, filename);
  await new Promise((res, rej) => {
    const w = createWriteStream(full);
    w.on('finish', res);
    w.on('error', rej);
    w.end(bytes);
  });
  return NextResponse.json({ path: `/photos/${filename}` });
}

