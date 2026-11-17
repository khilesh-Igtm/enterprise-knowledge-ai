"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, LockKeyhole, Mail } from "lucide-react";
import { toast } from "sonner";

import { register } from "@/features/auth/auth-service";

export function RegisterForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (password.length < 12) {
      toast.error("Password must contain at least 12 characters.");
      return;
    }

    if (password.length > 128) {
      toast.error("Password cannot exceed 128 characters.");
      return;
    }

    if (password !== confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);

      await register({
        email: email.trim().toLowerCase(),
        password,
      });

      toast.success("Account created. Please sign in.");
      router.push("/login");
    } catch (error: unknown) {
      const message =
        (
          error as {
            response?: { data?: { detail?: string } };
          }
        )?.response?.data?.detail || "Unable to create your account.";

      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <p className="mb-3 text-sm font-semibold text-indigo-600">
          GET STARTED
        </p>
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">
          Create your account
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Set up your workspace and start exploring your documents.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="register-email"
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
              id="register-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              className="h-12 w-full rounded-xl border border-slate-200 pl-11 pr-4 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="register-password"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Password
          </label>

          <div className="relative">
            <LockKeyhole
              size={18}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              id="register-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              minLength={12}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 12 characters"
              className="h-12 w-full rounded-xl border border-slate-200 pl-11 pr-12 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
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
          <p className="mt-1.5 text-xs text-slate-400">
            Use at least 12 characters.
          </p>
        </div>

        <div>
          <label
            htmlFor="confirm-password"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Confirm password
          </label>

          <input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            required
            maxLength={128}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="Enter your password again"
            className="h-12 w-full rounded-xl border border-slate-200 px-4 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading && <Loader2 size={18} className="animate-spin" />}
          {loading ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-slate-500">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-semibold text-indigo-600 hover:text-indigo-700"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}