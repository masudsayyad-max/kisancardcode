import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const cards = await prisma.card.findMany({ orderBy: { id: "desc" } });
  return NextResponse.json(cards);
}

export async function POST(req: NextRequest) {
  const data = await req.json();
  const card = await prisma.card.create({ data });
  return NextResponse.json(card, { status: 201 });
}

