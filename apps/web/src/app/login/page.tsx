import type { Metadata } from "next";

import { AuthLayout } from "@/features/auth/auth-layout";
import { LoginForm } from "@/features/auth/login-form";

export const metadata: Metadata = {
  title: "Sign In",
};

export default function LoginPage() {
  return (
    <AuthLayout mode="login">
      <LoginForm />
    </AuthLayout>
  );
}