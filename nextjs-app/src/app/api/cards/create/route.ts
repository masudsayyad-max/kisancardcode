import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyToken } from "@/lib/jwt";

export async function POST(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const me = verifyToken(token);
  if (!me) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const data = await req.json();
  // Wallet deduction (₹30)
  const user = await prisma.user.findUnique({ where: { id: me.id } });
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  if (user.wallet < 30) return NextResponse.json({ error: "Insufficient wallet" }, { status: 400 });

  const card = await prisma.$transaction(async (tx) => {
    await tx.user.update({ where: { id: user.id }, data: { wallet: { decrement: 30 } } });
    return tx.card.create({ data: { ...data, user_id: user.id } });
  });
  return NextResponse.json(card, { status: 201 });
}

