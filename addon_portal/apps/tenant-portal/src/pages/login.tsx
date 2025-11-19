/**
 * Tenant Portal Login Page
 * 
 * OTP-based authentication flow:
 * 1. Enter tenant slug
 * 2. Receive OTP
 * 3. Enter OTP
 * 4. Get session token
 */

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';
import { Navigation } from '../components/Navigation';
import { Breadcrumb } from '../components/Breadcrumb';

export default function LoginPage() {
  const router = useRouter();
  const { generateOTP, verifyOTP, error: authError } = useAuth();
  
  const [step, setStep] = useState<'slug' | 'otp'>('slug');
  const [tenantSlug, setTenantSlug] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpExpiresIn, setOtpExpiresIn] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSlugSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!tenantSlug.trim()) {
      setError('Please enter a tenant slug');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await generateOTP(tenantSlug.trim());
      setOtpExpiresIn(response.expires_in);
      setStep('otp');
      
      // Start countdown timer
      let remaining = response.expires_in;
      const timer = setInterval(() => {
        remaining -= 1;
        setOtpExpiresIn(remaining);
        if (remaining <= 0) {
          clearInterval(timer);
          setError('OTP expired. Please request a new one.');
          setStep('slug');
        }
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate OTP');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleOTPSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!otpCode.trim()) {
      setError('Please enter the OTP code');
      return;
    }

    setIsVerifying(true);
    setError(null);

    try {
      await verifyOTP(tenantSlug, otpCode.trim());
      // Redirect handled by useAuth hook
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid OTP code');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleBack = () => {
    setStep('slug');
    setOtpCode('');
    setOtpExpiresIn(null);
    setError(null);
  };

  const displayError = error || authError;

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
      <Navigation />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: 'Login' }]} />

        <div className="max-w-md mx-auto mt-12">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Q2O Tenant Portal
              </h1>
              <p className="text-gray-600">
                {step === 'slug' ? 'Enter your tenant slug to begin' : 'Enter the OTP code sent to you'}
              </p>
            </div>

            {displayError && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm font-medium">{displayError}</p>
              </div>
            )}

            {step === 'slug' ? (
              <form onSubmit={handleSlugSubmit}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="tenant-slug" className="block text-sm font-semibold text-gray-700 mb-2">
                      Tenant Slug
                    </label>
                    <input
                      id="tenant-slug"
                      type="text"
                      value={tenantSlug}
                      onChange={(e) => setTenantSlug(e.target.value)}
                      placeholder="e.g., demo, mycompany"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors text-base"
                      disabled={isGenerating}
                      autoFocus
                    />
                    <p className="mt-2 text-sm text-gray-500">
                      Your unique tenant identifier
                    </p>
                  </div>

                  <button
                    type="submit"
                    disabled={isGenerating || !tenantSlug.trim()}
                    className="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    {isGenerating ? 'Generating OTP...' : 'Request OTP'}
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleOTPSubmit}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="otp-code" className="block text-sm font-semibold text-gray-700 mb-2">
                      OTP Code
                    </label>
                    <input
                      id="otp-code"
                      type="text"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder="000000"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors text-base text-center text-2xl font-mono tracking-widest"
                      disabled={isVerifying}
                      maxLength={6}
                      autoFocus
                    />
                    {otpExpiresIn !== null && (
                      <p className="mt-2 text-sm text-gray-500">
                        Expires in: {Math.floor(otpExpiresIn / 60)}:{(otpExpiresIn % 60).toString().padStart(2, '0')}
                      </p>
                    )}
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={handleBack}
                      disabled={isVerifying}
                      className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={isVerifying || otpCode.length !== 6}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                      {isVerifying ? 'Verifying...' : 'Verify OTP'}
                    </button>
                  </div>
                </div>
              </form>
            )}

            <div className="mt-6 text-center text-sm text-gray-500">
              <p>Need help? Contact your administrator</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

