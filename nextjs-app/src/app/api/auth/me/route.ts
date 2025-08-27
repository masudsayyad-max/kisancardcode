import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/jwt";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const payload = verifyToken(token);
  if (!payload) return NextResponse.json({ user: null });
  const user = await prisma.user.findUnique({ where: { id: payload.id } });
  return NextResponse.json({ user: user ? { id: user.id, email: user.email, name: user.name, wallet: user.wallet, is_admin: user.is_admin } : null });
}

