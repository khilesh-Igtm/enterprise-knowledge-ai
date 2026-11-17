import type { Metadata } from "next";

import { AuthLayout } from "@/features/auth/auth-layout";
import { RegisterForm } from "@/features/auth/register-form";

export const metadata: Metadata = {
  title: "Create Account",
};

export default function RegisterPage() {
  return (
    <AuthLayout mode="register">
      <RegisterForm />
    </AuthLayout>
  );
}