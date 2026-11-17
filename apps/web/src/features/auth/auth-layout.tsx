import Link from "next/link";
import { BrainCircuit, ShieldCheck, Sparkles } from "lucide-react";

export function AuthLayout({
  children,
}: {
  children: React.ReactNode;
  mode: "login" | "register";
}) {
  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-[#111827] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-indigo-500/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-32 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />

        <Link href="/" className="relative z-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500">
            <BrainCircuit size={25} />
          </div>
          <span className="text-lg font-semibold tracking-tight">
            Enterprise Knowledge AI
          </span>
        </Link>

        <div className="relative z-10 max-w-lg">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-indigo-200">
            <Sparkles size={15} />
            Intelligent document workspace
          </div>

          <h1 className="text-5xl font-semibold leading-tight tracking-tight">
            Your knowledge.
            <br />
            <span className="text-indigo-300">One intelligent</span>
            <br />
            workspace.
          </h1>

          <p className="mt-6 max-w-md text-lg leading-8 text-slate-300">
            Bring your documents together, ask better questions, and
            discover insights with AI-powered knowledge retrieval.
          </p>

          <div className="mt-10 flex items-center gap-3 text-sm text-slate-300">
            <ShieldCheck size={19} className="text-emerald-400" />
            Private workspaces with secure access
          </div>
        </div>

        <p className="relative z-10 text-sm text-slate-500">
          © {new Date().getFullYear()} Enterprise Knowledge AI
        </p>
      </section>

      <section className="flex min-h-screen items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <Link
            href="/"
            className="mb-10 flex items-center gap-2 text-sm font-semibold text-slate-900 lg:hidden"
          >
            <BrainCircuit className="text-indigo-600" size={25} />
            Enterprise Knowledge AI
          </Link>

          {children}

          <p className="mt-10 text-center text-xs leading-5 text-slate-400">
            By continuing, you agree to use this workspace responsibly
            and keep your account credentials secure.
          </p>
        </div>
      </section>
    </main>
  );
}