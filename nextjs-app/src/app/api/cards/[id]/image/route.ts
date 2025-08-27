import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import QRCode from "qrcode";

async function svgForText(text: string, size: number, color: string, fontFamily: string, fontSize: number) {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return `<svg xmlns='http://www.w3.org/2000/svg' width='${size}' height='${size}'>
    <style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;700&display=swap');</style>
    <rect width='100%' height='100%' fill='white' />
    <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='${color}' font-family='${fontFamily}' font-size='${fontSize}'>${esc(text)}</text>
  </svg>`;
}

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  const id = Number(params.id);
  const card = await prisma.card.findUnique({ where: { id } });
  if (!card) return new NextResponse("Not found", { status: 404 });

  const qrPayload = `${card.farmer_id ?? ''}|${card.name_en ?? ''}|${card.mobile ?? ''}|${card.aadhaar ?? ''}`;
  const qrPng = await QRCode.toBuffer(qrPayload, { width: 600, margin: 1 });

  // Simple SVG-based preview page rendering text (Devanagari via Google Fonts)
  const titleSvg = await svgForText(`नाव: ${card.name_mr ?? ''}`, 1200, "#1c3d2b", "'Noto Sans Devanagari', sans-serif", 64);

  const boundary = "NEXTFORM-DASH-BOUNDARY";
  const body = Buffer.concat([
    Buffer.from(titleSvg),
  ]);
  return new NextResponse(body, { headers: { "Content-Type": "image/svg+xml" } });
}

