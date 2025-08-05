import { Suspense } from "react";
import SiteAnalysisWrapper from "./SiteAnalysisWrapper";

export default function SiteAnalysisPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    }>
      <SiteAnalysisWrapper />
    </Suspense>
  );
}