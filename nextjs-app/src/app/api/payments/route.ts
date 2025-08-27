import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyToken } from "@/lib/jwt";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const me = verifyToken(token);
  if (!me) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const payments = await prisma.payment.findMany({ where: { user_id: me.id }, orderBy: { id: "desc" } });
  return NextResponse.json(payments);
}

export async function POST(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const me = verifyToken(token);
  if (!me) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { amount, utr } = await req.json();
  if (Number(amount) < 50) return NextResponse.json({ error: "Minimum ₹50" }, { status: 400 });
  const txn = await prisma.payment.create({ data: {
    user_id: me.id,
    date: new Date().toISOString().slice(0,19).replace('T',' '),
    amount: Number(amount),
    utr: utr || '',
    status: 'Pending',
    note: 'Waiting for admin approval'
  }});
  return NextResponse.json(txn, { status: 201 });
}

