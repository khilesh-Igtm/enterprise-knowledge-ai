import { api } from "@/lib/api";
import type {
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  User,
} from "@/types/auth";

export async function login(
  payload: LoginPayload,
): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>(
    "/auth/login",
    payload,
  );

  return data;
}

export async function register(
  payload: RegisterPayload,
): Promise<User> {
  const { data } = await api.post<User>(
    "/auth/register",
    payload,
  );

  return data;
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function logout(refreshToken: string): Promise<void> {
  await api.post("/auth/logout", {
    refresh_token: refreshToken,
  });
}