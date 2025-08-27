import jwt from "jsonwebtoken";

const secret = process.env.JWT_SECRET || "dev_secret";

export type JwtPayload = { id: number; email: string; is_admin?: boolean };

export function signToken(payload: JwtPayload, expiresIn: string = "7d") {
  return jwt.sign(payload, secret, { expiresIn });
}

export function verifyToken<T = JwtPayload>(token?: string | null): T | null {
  if (!token) return null;
  try {
    return jwt.verify(token, secret) as T;
  } catch {
    return null;
  }
}

