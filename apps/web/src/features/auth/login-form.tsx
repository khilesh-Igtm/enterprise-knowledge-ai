"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, LockKeyhole, Mail } from "lucide-react";
import { toast } from "sonner";

import { login, getCurrentUser } from "@/features/auth/auth-service";
import { useAuthStore } from "@/features/auth/auth-store";
import { saveTokens } from "@/lib/auth-token";

export function LoginForm() {
  const router = useRouter();
  const setUser = useAuthStore((state) => state.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim() || !password) {
      toast.error("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const tokens = await login({
        email: email.trim().toLowerCase(),
        password,
      });

      saveTokens(tokens);

      const user = await getCurrentUser();
      setUser(user);

      toast.success("Welcome back!");
      router.replace("/dashboard");
    } catch (error: unknown) {
      const message =
        (
          error as {
            response?: { data?: { detail?: string } };
          }
        )?.response?.data?.detail || "Unable to sign in. Please try again.";

      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <p className="mb-3 text-sm font-semibold text-indigo-600">
          WELCOME BACK
        </p>
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">
          Sign in to your account
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Access your knowledge bases and AI conversations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label
            htmlFor="email"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Email address
          </label>

          <div className="relative">
            <Mail
              size={18}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
            />
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <label
              htmlFor="password"
              className="text-sm font-medium text-slate-700"
            >
              Password
            </label>
          </div>

          <div className="relative">
            <LockKeyhole
              size={18}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-12 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
            />
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading && <Loader2 size={18} className="animate-spin" />}
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-slate-500">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="font-semibold text-indigo-600 hover:text-indigo-700"
        >
          Create account
        </Link>
      </p>
    </div>
  );
}