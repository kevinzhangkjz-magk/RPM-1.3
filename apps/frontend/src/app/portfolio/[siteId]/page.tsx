"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import Link from "next/link";
import { ArrowLeft, TrendingUp } from "lucide-react";
import { ScatterChart, Scatter, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from "recharts";
import { sitesApi, sitesQueryKeys } from "@/lib/api/sites";
import { calculateRMSE, calculateRSquared } from "@/lib/utils";

export default function SiteAnalysisPage() {
  const params = useParams();
  const siteId = params.siteId as string;
  
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

  // Calculate client-side metrics if backend doesn't provide them
  const rmse = performanceData ? calculateRMSE(performanceData.data_points) : 0;
  const rSquared = performanceData ? calculateRSquared(performanceData.data_points) : 0;

  // Prepare chart data - convert kW to MW
  const chartData = performanceData?.data_points.map((point, index) => ({
    id: index,
    poa_irradiance: point.poa_irradiance,
    actual_power: point.actual_power / 1000, // Convert kW to MW
    expected_power: point.expected_power / 1000, // Convert kW to MW
  })) || [];

  // Create sorted data for trend line rendering
  const sortedChartData = [...chartData].sort((a, b) => a.poa_irradiance - b.poa_irradiance);

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
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
          
          <h1 className="text-4xl font-bold mb-2">
            Power Curve - Site: {siteId}
          </h1>
          <p className="text-xl text-muted-foreground">
            Actual vs. Expected Performance Analysis
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Chart Section */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>Power Curve Visualization</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
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
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">RMSE</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {isLoading ? "..." : `${rmse.toFixed(1)} MW`}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">R-Squared</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {isLoading ? "..." : rSquared.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Skid Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Skid 01</span>
                    <span className="text-red-500">-5.1%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Skid 02</span>
                    <span className="text-green-500">+2.3%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Skid 03</span>
                    <span className="text-yellow-500">-0.8%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
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