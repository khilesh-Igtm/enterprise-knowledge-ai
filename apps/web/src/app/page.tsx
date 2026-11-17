"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { BrainCircuit, LoaderCircle } from "lucide-react";

import { useAuthStore } from "@/features/auth/auth-store";

export default function Home() {
  const router = useRouter();

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated,
  );
  const isInitialized = useAuthStore(
    (state) => state.isInitialized,
  );

  useEffect(() => {
    if (!isInitialized) return;

    router.replace(isAuthenticated ? "/dashboard" : "/login");
  }, [isInitialized, isAuthenticated, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/20">
          <BrainCircuit size={30} />
        </div>

        <h1 className="text-lg font-semibold text-slate-900">
          Enterprise Knowledge AI
        </h1>

        <div className="mt-5 flex items-center gap-2 text-sm text-slate-500">
          <LoaderCircle size={16} className="animate-spin" />
          Loading your workspace...
        </div>
      </div>
    </main>
  );
}