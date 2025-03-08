import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md">
        <SignIn
          path="/auth/login"
          routing="path"
          signUpUrl="/auth/signup"
          redirectUrl="/dashboard"
        />
      </div>
    </div>
  );
} 