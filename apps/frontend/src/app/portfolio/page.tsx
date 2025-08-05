"use client";

import { useQuery } from "@tanstack/react-query";
import { sitesApi, sitesQueryKeys } from "../../lib/api/sites";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowRight, MapPin, Zap, Calendar, AlertCircle } from "lucide-react";

export default function PortfolioPage() {
  const {
    data: sitesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: sitesQueryKeys.lists(),
    queryFn: sitesApi.getSites,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-lg text-muted-foreground">Loading sites...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-2">Error Loading Sites</h2>
              <p className="text-muted-foreground mb-4">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <Button onClick={() => window.location.reload()}>
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const sites = sitesData?.sites || [];

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Site Portfolio</h1>
          <p className="text-xl text-muted-foreground">
            Manage and monitor all your solar sites
          </p>
          <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Zap className="h-4 w-4" />
              {sites.length} Active Sites
            </span>
            <span className="flex items-center gap-1">
              <Zap className="h-4 w-4" />
              {sites.reduce((total, site) => total + (site.capacity_kw || 0), 0).toLocaleString()} MW Total Capacity
            </span>
          </div>
        </div>

        {/* Sites Grid */}
        {sites.length === 0 ? (
          <div className="text-center py-16">
            <Zap className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-semibold mb-2">No Sites Found</h2>
            <p className="text-muted-foreground mb-4">
              There are no active solar sites to display.
            </p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sites.map((site) => (
              <div
                key={site.site_id}
                className="border rounded-lg p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-1">
                      {site.site_name || site.site_id}
                    </h3>
                    <p className="text-sm text-muted-foreground font-mono">
                      {site.site_id}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <div 
                      className={`w-2 h-2 rounded-full ${
                        site.connectivity_status === 'connected' 
                          ? 'bg-green-500' 
                          : 'bg-red-500'
                      }`}
                      title={site.connectivity_status === 'connected' ? 'Connected' : 'Disconnected'}
                    ></div>
                  </div>
                </div>

                <div className="space-y-2 mb-6">
                  {site.location && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      {site.location}
                    </div>
                  )}
                  {site.capacity_kw && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Zap className="h-4 w-4" />
                      {site.capacity_kw.toLocaleString()} MW
                    </div>
                  )}
                  {site.installation_date && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      {new Date(site.installation_date).toLocaleDateString()}
                    </div>
                  )}
                </div>

                <Link href={`/site?id=${site.site_id}`}>
                  <Button className="w-full" variant="outline">
                    View Performance
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 flex justify-center">
          <Link href="/">
            <Button variant="outline">
              Back to Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}