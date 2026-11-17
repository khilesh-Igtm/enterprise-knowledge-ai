import axios, {
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from "@/lib/auth-token";

import type { TokenResponse } from "@/types/auth";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

const refreshClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 15000,
});

let refreshPromise: Promise<string> | null = null;

api.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    throw new Error("Refresh token not found");
  }

  const response = await refreshClient.post<TokenResponse>(
    "/auth/refresh",
    {
      refresh_token: refreshToken,
    },
  );

  saveTokens(response.data);

  return response.data.access_token;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | RetryableRequest
      | undefined;

    if (!originalRequest || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    const url = originalRequest.url || "";

    const isAuthRequest =
      url.includes("/auth/login") ||
      url.includes("/auth/register") ||
      url.includes("/auth/refresh") ||
      url.includes("/auth/logout");

    if (isAuthRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      const newAccessToken = await refreshPromise;

      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`;

      return api(originalRequest);
    } catch (refreshError) {
      clearTokens();

      if (typeof window !== "undefined") {
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.href = "/login";
      }

      return Promise.reject(refreshError);
    }
  },
);