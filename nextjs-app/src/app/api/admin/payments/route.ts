import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyToken } from "@/lib/jwt";

function requireAdmin(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const me = verifyToken<{ id: number; email: string; is_admin?: boolean }>(token);
  if (!me || !me.is_admin) return null;
  return me;
}

export async function GET(req: NextRequest) {
  const me = requireAdmin(req);
  if (!me) return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  const payments = await prisma.payment.findMany({ orderBy: { id: "desc" }, include: { user: true } });
  return NextResponse.json(payments);
}

export async function PUT(req: NextRequest) {
  const me = requireAdmin(req);
  if (!me) return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  const { id, action } = await req.json();
  const txn = await prisma.payment.findUnique({ where: { id } });
  if (!txn || txn.status !== 'Pending') return NextResponse.json({ error: 'Invalid transaction' }, { status: 400 });
  if (action === 'approve') {
    await prisma.$transaction([
      prisma.payment.update({ where: { id }, data: { status: 'Success', note: 'Your payment has been approved successfully.' } }),
      prisma.user.update({ where: { id: txn.user_id }, data: { wallet: { increment: txn.amount } } })
    ]);
  } else if (action === 'reject') {
    await prisma.payment.update({ where: { id }, data: { status: 'Rejected', note: 'Your payment request has been rejected due to the wrong UTR ID.' } });
  }
  return NextResponse.json({ ok: true });
}

