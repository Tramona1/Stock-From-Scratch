import { SignUp } from '@clerk/nextjs';

export default function SignUpPage() {
  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md">
        <SignUp
          path="/auth/signup"
          routing="path"
          signInUrl="/auth/login"
          redirectUrl="/dashboard"
        />
      </div>
    </div>
  );
} 