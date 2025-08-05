"use client";

import { useEffect, useState } from "react";
import { AlertCircle, X } from "lucide-react";

export function DemoBanner() {
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    // Check if we're using mock data
    const isNetlify = window.location.hostname.includes('netlify.app');
    // Runtime API URL detection
    const getApiUrl = () => {
      if (typeof window !== 'undefined') {
        if (window.location.hostname === 'frabjous-cuchufli-daaafb.netlify.app' || 
            window.location.hostname.includes('netlify.app')) {
          return 'https://rpm-13-production-ca68.up.railway.app';
        }
      }
      return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    };
    
    const apiUrl = getApiUrl();
    const apiIsLocalhost = apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1');
    
    if (isNetlify && apiIsLocalhost && !isDismissed) {
      setIsVisible(true);
    }
  }, [isDismissed]);

  if (!isVisible) return null;

  return (
    <div className="bg-yellow-50 border-b border-yellow-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <p className="text-sm text-yellow-800">
              <span className="font-medium">Demo Mode:</span> This site is using mock data. To connect to a real API, please configure the backend endpoint.
            </p>
          </div>
          <button
            onClick={() => {
              setIsVisible(false);
              setIsDismissed(true);
            }}
            className="text-yellow-600 hover:text-yellow-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}