import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import QRCode from "qrcode";
import { PDFDocument, StandardFonts, rgb } from "pdf-lib";

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  const card = await prisma.card.findUnique({ where: { id: Number(params.id) } });
  if (!card) return new NextResponse("Not found", { status: 404 });

  const mm = (v: number) => (v / 25.4) * 72; // convert mm to PDF points
  const pdf = await PDFDocument.create();
  const page1 = pdf.addPage([mm(86), mm(54)]);
  const page2 = pdf.addPage([mm(86), mm(54)]);

  const font = await pdf.embedFont(StandardFonts.Helvetica);
  const color = rgb(28/255, 61/255, 43/255);

  // QR
  const qrPayload = `${card.farmer_id ?? ''}|${card.name_en ?? ''}|${card.mobile ?? ''}|${card.aadhaar ?? ''}`;
  const qrPng = await QRCode.toBuffer(qrPayload, { width: 500, margin: 0 });
  const qrImg = await pdf.embedPng(qrPng);

  // FRONT
  page1.drawText(`Name: ${card.name_en ?? ''}` , { x: 10, y: mm(54) - 30, size: 10, font, color });
  page1.drawText(`नाव: ${card.name_mr ?? ''}` , { x: 10, y: mm(54) - 45, size: 10, font, color });
  page1.drawImage(qrImg, { x: mm(86) - 42, y: mm(54) - 42, width: 36, height: 36 });

  // BACK
  page2.drawText(`Address (EN): ${card.address_en ?? ''}`, { x: 10, y: mm(54) - 30, size: 10, font, color });
  page2.drawText(`पत्ता (MR): ${card.address_mr ?? ''}`, { x: 10, y: mm(54) - 45, size: 10, font, color });
  page2.drawImage(qrImg, { x: mm(86) - 42, y: mm(54) - 42, width: 36, height: 36 });

  const bytes = await pdf.save();
  return new NextResponse(Buffer.from(bytes), { headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': `attachment; filename=card_${card.id}.pdf` } });
}

