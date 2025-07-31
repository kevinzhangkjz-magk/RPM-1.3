"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import Link from "next/link";
import { ArrowLeft, TrendingUp, BarChart3 } from "lucide-react";
import { Scatter, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, BarChart, Bar, Cell } from "recharts";
import { sitesApi, sitesQueryKeys } from "@/lib/api/sites";
import { calculateRMSE, calculateRSquared } from "@/lib/utils";

export default function SiteAnalysisPage() {
  const params = useParams();
  const siteId = params.siteId as string;
  
  // View state - toggle between site-level and skid-level views
  const [viewMode, setViewMode] = useState<'site' | 'skids'>('site');
  
  // Toggle states for chart visibility
  const [showActual, setShowActual] = useState(true);
  const [showExpected, setShowExpected] = useState(true);
  const [showTrendLine, setShowTrendLine] = useState(true);

  // Fetch site data for connectivity status
  const { data: sitesData } = useQuery({
    queryKey: sitesQueryKeys.lists(),
    queryFn: sitesApi.getSites,
  });

  // Find current site data
  const currentSite = sitesData?.sites.find(site => site.site_id === siteId);

  // Fetch site performance data
  const { data: performanceData, isLoading, error } = useQuery({
    queryKey: sitesQueryKeys.sitePerformance(siteId),
    queryFn: () => sitesApi.getSitePerformance(siteId),
  });

  // Fetch skids data for the skid-level view
  const { data: skidsData, isLoading: skidsLoading, error: skidsError } = useQuery({
    queryKey: sitesQueryKeys.siteSkids(siteId),
    queryFn: () => sitesApi.getSiteSkids(siteId),
    enabled: viewMode === 'skids', // Only fetch when in skids view
  });

  // Calculate client-side metrics if backend doesn't provide them - memoized for performance
  const metrics = useMemo(() => {
    if (!performanceData) return { rmse: 0, rSquared: 0 };
    return {
      rmse: calculateRMSE(performanceData.data_points),
      rSquared: calculateRSquared(performanceData.data_points)
    };
  }, [performanceData]);

  // Prepare chart data - convert kW to MW - memoized for performance
  const chartData = useMemo(() => {
    return performanceData?.data_points.map((point, index) => ({
      id: index,
      poa_irradiance: point.poa_irradiance,
      actual_power: point.actual_power / 1000, // Convert kW to MW
      expected_power: point.expected_power / 1000, // Convert kW to MW
    })) || [];
  }, [performanceData]);

  // Create sorted data for trend line rendering - memoized for performance
  const sortedChartData = useMemo(() => {
    return [...chartData].sort((a, b) => a.poa_irradiance - b.poa_irradiance);
  }, [chartData]);

  // Prepare skids chart data - memoized for performance
  const skidsChartData = useMemo(() => {
    return skidsData?.skids?.map(skid => ({
      ...skid,
      avg_actual_power_mw: skid.avg_actual_power / 1000,
      avg_expected_power_mw: skid.avg_expected_power / 1000
    })) || [];
  }, [skidsData]);

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            {viewMode === 'skids' ? (
              <Button variant="outline" size="sm" onClick={() => setViewMode('site')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Site Analysis
              </Button>
            ) : (
              <Link href="/portfolio">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Portfolio
                </Button>
              </Link>
            )}
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                currentSite?.connectivity_status === 'connected' 
                  ? 'bg-green-500' 
                  : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-muted-foreground">
                {currentSite?.connectivity_status === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          {/* Breadcrumbs */}
          <div className="text-sm text-muted-foreground mb-4">
            {viewMode === 'skids' ? (
              <span>Portfolio &gt; {currentSite?.site_name || siteId} &gt; Skids</span>
            ) : (
              <span>Portfolio &gt; {currentSite?.site_name || siteId}</span>
            )}
          </div>
          
          <h1 className="text-4xl font-bold mb-2">
            {viewMode === 'skids' 
              ? `Skid Performance - Site: ${siteId}`
              : `Power Curve - Site: ${siteId}`
            }
          </h1>
          <p className="text-xl text-muted-foreground">
            {viewMode === 'skids'
              ? 'Comparative Analysis of All Skids'
              : 'Actual vs. Expected Performance Analysis'
            }
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Chart Section */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>
                  {viewMode === 'skids' ? 'Skid Comparative Analysis' : 'Power Curve Visualization'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {viewMode === 'site' ? (
                  // Site-level Power Curve Chart
                  isLoading ? (
                    <div className="h-96 flex items-center justify-center">
                      <div className="text-center">
                        <TrendingUp className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground">Loading performance data...</p>
                      </div>
                    </div>
                  ) : error ? (
                    <div className="h-96 flex items-center justify-center">
                      <div className="text-center">
                        <p className="text-red-500 mb-2">Error loading data</p>
                        <p className="text-sm text-muted-foreground">{error.message}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="h-96">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="poa_irradiance" 
                            label={{ value: 'POA Irradiance (W/m²)', position: 'insideBottom', offset: -10 }}
                          />
                          <YAxis 
                            label={{ value: 'Power (MW)', angle: -90, position: 'insideLeft' }}
                          />
                          <Tooltip 
                            formatter={(value, name) => {
                              // Skip rendering poa_irradiance in the content
                              if (name === 'poa_irradiance') return null;
                              
                              const formattedValue = typeof value === 'number' ? value.toFixed(3) : value;
                              const formattedName = name === 'actual_power' ? 'Actual Power' : 
                                                  name === 'expected_power' ? 'Expected Power' : 
                                                  name === 'trend_power' ? 'Expected Trend' : name;
                              return [formattedValue, formattedName];
                            }}
                            labelFormatter={(value) => `POA Irradiance: ${value} W/m²`}
                            content={(props) => {
                              const { active, payload, label } = props;
                              if (active && payload && payload.length) {
                                return (
                                  <div className="bg-white p-2 border rounded shadow-sm">
                                    <p className="font-medium">{`POA Irradiance: ${label} W/m²`}</p>
                                    {payload
                                      .filter(entry => entry.dataKey !== 'poa_irradiance')
                                      .map((entry, index) => {
                                        const value = typeof entry.value === 'number' ? entry.value.toFixed(3) : entry.value;
                                        let displayName = entry.name;
                                        if (entry.dataKey === 'actual_power') displayName = 'Actual Power';
                                        else if (entry.dataKey === 'expected_power' && entry.name === 'Expected Power') displayName = 'Expected Power';
                                        else if (entry.dataKey === 'expected_power' && entry.name === 'Expected Trend') displayName = 'Expected Trend';
                                        
                                        const unit = entry.dataKey === 'actual_power' || entry.dataKey === 'expected_power' ? ' MW' : '';
                                        return (
                                          <p key={index} style={{ color: entry.color }}>
                                            {`${displayName} : ${value}${unit}`}
                                          </p>
                                        );
                                      })}
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Legend />
                          
                          {/* Scatter plots for actual and expected power */}
                          {showActual && (
                            <Scatter 
                              dataKey="actual_power" 
                              fill="#3b82f6" 
                              name="Actual Power"
                            />
                          )}
                          
                          {showExpected && (
                            <Scatter 
                              dataKey="expected_power" 
                              fill="#6b7280" 
                              name="Expected Power"
                            />
                          )}
                          
                          {/* Trend line - uses expected_power with sorted data */}
                          {showTrendLine && (
                            <Line 
                              data={sortedChartData}
                              dataKey="expected_power" 
                              stroke="#ef4444" 
                              strokeWidth={3}
                              dot={false}
                              name="Expected Trend"
                              connectNulls={false}
                              type="monotone"
                            />
                          )}
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  )
                ) : (
                  // Skids-level Comparative Chart
                  skidsLoading ? (
                    <div className="h-96 flex items-center justify-center">
                      <div className="text-center">
                        <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground">Loading skids data...</p>
                      </div>
                    </div>
                  ) : skidsError ? (
                    <div className="h-96 flex items-center justify-center">
                      <div className="text-center">
                        <p className="text-red-500 mb-2">Error loading skids data</p>
                        <p className="text-sm text-muted-foreground">{skidsError.message}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="h-96">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={skidsChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="skid_name" 
                            label={{ value: 'Skids', position: 'insideBottom', offset: -10 }}
                          />
                          <YAxis 
                            label={{ value: 'Power (MW)', angle: -90, position: 'insideLeft' }}
                          />
                          <Tooltip 
                            content={(props) => {
                              const { active, payload, label } = props;
                              if (active && payload && payload.length && payload[0].payload) {
                                const data = payload[0].payload;
                                return (
                                  <div className="bg-white p-3 border rounded shadow-sm">
                                    <p className="font-medium mb-2">{label}</p>
                                    <div className="space-y-1">
                                      <p className="text-blue-600">
                                        Actual Power: {data.avg_actual_power_mw?.toFixed(3)} MW
                                      </p>
                                      <p className="text-gray-600">
                                        Expected Power: {data.avg_expected_power_mw?.toFixed(3)} MW
                                      </p>
                                      <p className={`font-medium ${
                                        data.deviation_percentage < -2 ? 'text-red-600' : 
                                        data.deviation_percentage > 0 ? 'text-green-600' : 'text-yellow-600'
                                      }`}>
                                        Deviation: {data.deviation_percentage?.toFixed(1)}%
                                      </p>
                                      <p className="text-xs text-muted-foreground">
                                        Data Points: {data.data_point_count}
                                      </p>
                                    </div>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Legend />
                          <Bar 
                            dataKey="avg_actual_power_mw" 
                            name="Actual Power"
                          >
                            {skidsChartData.map((skid, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={skid.deviation_percentage < -2 ? "#dc2626" : "#3b82f6"}
                              />
                            ))}
                          </Bar>
                          <Bar 
                            dataKey="avg_expected_power_mw" 
                            fill="#6b7280" 
                            name="Expected Power"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )
                )}
              </CardContent>
            </Card>

            {/* Chart Controls */}
            <Card className="mt-4">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={showActual} 
                        onCheckedChange={setShowActual}
                        id="toggle-actual"
                      />
                      <label htmlFor="toggle-actual" className="text-sm font-medium">
                        Actual Data
                      </label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={showExpected} 
                        onCheckedChange={setShowExpected}
                        id="toggle-expected"
                      />
                      <label htmlFor="toggle-expected" className="text-sm font-medium">
                        Expected Data
                      </label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={showTrendLine} 
                        onCheckedChange={setShowTrendLine}
                        id="toggle-trend"
                      />
                      <label htmlFor="toggle-trend" className="text-sm font-medium">
                        Trend Line
                      </label>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      POA
                    </Button>
                    <Button variant="ghost" size="sm">
                      GHI
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* KPI Cards Sidebar */}
          <div className="space-y-6">
            {viewMode === 'site' ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">RMSE</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold">
                      {isLoading ? "..." : `${metrics.rmse.toFixed(1)} MW`}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">R-Squared</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold">
                      {isLoading ? "..." : metrics.rSquared.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Skid Performance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {isLoading ? (
                      <div className="space-y-2 text-sm">
                        <div className="animate-pulse">Loading skids...</div>
                      </div>
                    ) : (
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground mb-2">Click to view detailed comparison</span>
                        </div>
                        {performanceData?.data_points ? (
                          // Simulate skid data from performance data for now
                          ['Skid 01', 'Skid 02', 'Skid 03'].map((skidName, index) => (
                            <div 
                              key={skidName}
                              className="flex justify-between items-center p-2 rounded hover:bg-muted cursor-pointer transition-colors"
                              onClick={() => setViewMode('skids')}
                            >
                              <span>{skidName}</span>
                              <span className={
                                index === 0 ? "text-red-500" :
                                index === 1 ? "text-green-500" : "text-yellow-500"
                              }>
                                {index === 0 ? "-5.1%" : index === 1 ? "+2.3%" : "-0.8%"}
                              </span>
                            </div>
                          ))
                        ) : (
                          <div className="text-muted-foreground text-xs">No data available</div>
                        )}
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="w-full mt-3"
                          onClick={() => setViewMode('skids')}
                        >
                          View All Skids
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Site Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Total Skids:</span>
                        <span className="font-medium">{skidsData?.total_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Connected:</span>
                        <span className="font-medium text-green-500">
                          {currentSite?.connectivity_status === 'connected' ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Average Deviation:</span>
                        <span className="font-medium">
                          {skidsData?.skids ? 
                            `${(skidsData.skids.reduce((acc, skid) => acc + skid.deviation_percentage, 0) / skidsData.skids.length).toFixed(1)}%`
                            : 'N/A'
                          }
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Underperforming Skids</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {skidsData?.skids ? (
                        skidsData.skids
                          .filter(skid => skid.deviation_percentage < -2) // Skids with >2% negative deviation
                          .slice(0, 5) // Show top 5 worst performers
                          .map((skid) => (
                            <div key={skid.skid_id} className="flex justify-between items-center p-2 rounded bg-red-50">
                              <span>{skid.skid_name}</span>
                              <span className="text-red-600 font-medium">
                                {skid.deviation_percentage.toFixed(1)}%
                              </span>
                            </div>
                          ))
                      ) : (
                        <div className="text-muted-foreground">No underperforming skids found</div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Top Performers</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {skidsData?.skids ? (
                        skidsData.skids
                          .filter(skid => skid.deviation_percentage > 0) // Positive deviation
                          .sort((a, b) => b.deviation_percentage - a.deviation_percentage)
                          .slice(0, 3)
                          .map((skid) => (
                            <div key={skid.skid_id} className="flex justify-between items-center p-2 rounded bg-green-50">
                              <span>{skid.skid_name}</span>
                              <span className="text-green-600 font-medium">
                                +{skid.deviation_percentage.toFixed(1)}%
                              </span>
                            </div>
                          ))
                      ) : (
                        <div className="text-muted-foreground">No data available</div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
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