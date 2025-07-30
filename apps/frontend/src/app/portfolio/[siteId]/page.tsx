"use client";

import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft, Zap, MapPin, Calendar, TrendingUp } from "lucide-react";

export default function SiteAnalysisPage() {
  const params = useParams();
  const siteId = params.siteId as string;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Link href="/portfolio">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Portfolio
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-muted-foreground">Active</span>
            </div>
          </div>
          
          <h1 className="text-4xl font-bold mb-2">
            Site Analysis: {siteId}
          </h1>
          <p className="text-xl text-muted-foreground">
            Performance data and power curve analysis
          </p>
        </div>

        {/* Site Info Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-5 w-5 text-blue-600" />
              <h3 className="font-semibold">Capacity</h3>
            </div>
            <p className="text-2xl font-bold">5,000 kW</p>
            <p className="text-sm text-muted-foreground">Total installed capacity</p>
          </div>
          
          <div className="border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="h-5 w-5 text-green-600" />
              <h3 className="font-semibold">Location</h3>
            </div>
            <p className="text-2xl font-bold">Arizona</p>
            <p className="text-sm text-muted-foreground">Site location</p>
          </div>
          
          <div className="border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="h-5 w-5 text-purple-600" />
              <h3 className="font-semibold">Installed</h3>
            </div>
            <p className="text-2xl font-bold">2023</p>
            <p className="text-sm text-muted-foreground">Installation year</p>
          </div>
        </div>

        {/* Placeholder for Performance Data */}
        <div className="border rounded-lg p-8 text-center">
          <TrendingUp className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Performance Data</h2>
          <p className="text-muted-foreground mb-4">
            Detailed performance analysis and power curve visualization will be implemented in future stories.
          </p>
          <p className="text-sm text-muted-foreground">
            This page will integrate with the backend API endpoint: 
            <code className="bg-muted px-2 py-1 rounded ml-1">
              GET /api/sites/{siteId}/performance
            </code>
          </p>
        </div>

        {/* Navigation */}
        <div className="mt-8 flex justify-between">
          <Link href="/portfolio">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Portfolio
            </Button>
          </Link>
          
          <div className="flex gap-2">
            <Button variant="outline" disabled>
              Export Data
            </Button>
            <Button disabled>
              View Report
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}