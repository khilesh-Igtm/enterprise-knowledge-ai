"use client";

import { useEffect } from "react";

import { getAccessToken, getRefreshToken } from "@/lib/auth-token";
import { getCurrentUser } from "@/features/auth/auth-service";
import { useAuthStore } from "@/features/auth/auth-store";

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const setUser = useAuthStore((state) => state.setUser);
  const setInitialized = useAuthStore(
    (state) => state.setInitialized,
  );

  useEffect(() => {
    let active = true;

    async function initializeAuth() {
      const accessToken = getAccessToken();
      const refreshToken = getRefreshToken();

      if (!accessToken && !refreshToken) {
        if (active) {
          setUser(null);
          setInitialized(true);
        }
        return;
      }

      try {
        const user = await getCurrentUser();

        if (active) {
          setUser(user);
        }
      } catch {
        if (active) {
          setUser(null);
        }
      } finally {
        if (active) {
          setInitialized(true);
        }
      }
    }

    void initializeAuth();

    return () => {
      active = false;
    };
  }, [setUser, setInitialized]);

  return <>{children}</>;
}