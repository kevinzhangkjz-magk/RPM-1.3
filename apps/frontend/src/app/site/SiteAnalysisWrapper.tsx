"use client";

import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import Link from "next/link";
import { ArrowLeft, TrendingUp, BarChart3 } from "lucide-react";
import { Scatter, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, BarChart, Bar, Cell } from "recharts";
import { sitesApi, sitesQueryKeys } from "../../lib/api/sites";
import { calculateRMSE, calculateRSquared } from "../../lib/utils";

export default function SiteAnalysisWrapper() {
  const searchParams = useSearchParams();
  const siteId = searchParams.get('id') || '1';
  
  // View state - toggle between site-level and skid-level views
  const [viewMode, setViewMode] = useState<'site' | 'skids'>('site');

  // Fetch site performance data
  const {
    data: siteData,
    isLoading: siteLoading,
    error: siteError,
  } = useQuery({
    queryKey: sitesQueryKeys.detail(siteId),
    queryFn: () => sitesApi.getSitePerformance(siteId),
  });

  const { actualData, predictedData, combinedData, rmse, rSquared } = useMemo(() => {
    if (!siteData?.data) {
      return {
        actualData: [],
        predictedData: [],
        combinedData: [],
        rmse: 0,
        rSquared: 0,
      };
    }

    const data = siteData.data;
    
    // Site-level view: aggregate all skids
    if (viewMode === 'site') {
      // Group by date and sum power across all skids
      const dailyTotals = data.reduce((acc: any, curr: any) => {
        const date = curr.date;
        if (!acc[date]) {
          acc[date] = { 
            date, 
            actual_power: 0, 
            predicted_power: 0,
            skids: new Set()
          };
        }
        acc[date].actual_power += curr.actual_power;
        acc[date].predicted_power += curr.predicted_power;
        acc[date].skids.add(curr.skid_id);
        return acc;
      }, {});

      const aggregatedData = Object.values(dailyTotals).map((item: any) => ({
        date: item.date,
        actual_power: item.actual_power,
        predicted_power: item.predicted_power,
        skid_count: item.skids.size
      }));

      const actualValues = aggregatedData.map((d: any) => d.actual_power);
      const predictedValues = aggregatedData.map((d: any) => d.predicted_power);

      return {
        actualData: aggregatedData.map((d: any) => ({ x: d.date, y: d.actual_power })),
        predictedData: aggregatedData.map((d: any) => ({ x: d.date, y: d.predicted_power })),
        combinedData: aggregatedData,
        rmse: calculateRMSE(actualValues, predictedValues),
        rSquared: calculateRSquared(actualValues, predictedValues),
      };
    } else {
      // Skid-level view: show individual skids
      const actualValues = data.map((d: any) => d.actual_power);
      const predictedValues = data.map((d: any) => d.predicted_power);

      return {
        actualData: data.map((d: any) => ({ x: d.date, y: d.actual_power, skid: d.skid_id })),
        predictedData: data.map((d: any) => ({ x: d.date, y: d.predicted_power, skid: d.skid_id })),
        combinedData: data,
        rmse: calculateRMSE(actualValues, predictedValues),
        rSquared: calculateRSquared(actualValues, predictedValues),
      };
    }
  }, [siteData, viewMode]);

  if (siteLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (siteError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <span>Error Loading Site Data</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Unable to load performance data for Site {siteId}. Please try again or contact support.
            </p>
            <Link href="/portfolio">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Portfolio
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/portfolio">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Portfolio
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Site {siteId} Performance Analysis
                </h1>
                <p className="text-sm text-gray-500">
                  Predictive analytics and performance metrics
                </p>
              </div>
            </div>
            
            {/* View Toggle */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-700">View:</span>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${viewMode === 'site' ? 'font-medium' : 'text-gray-500'}`}>
                  Site Level
                </span>
                <Switch 
                  checked={viewMode === 'skids'} 
                  onCheckedChange={(checked) => setViewMode(checked ? 'skids' : 'site')}
                />
                <span className={`text-sm ${viewMode === 'skids' ? 'font-medium' : 'text-gray-500'}`}>
                  Skid Level
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Model Accuracy (R²)
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(rSquared * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Coefficient of determination
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                RMSE
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {rmse.toFixed(1)}
              </div>
              <p className="text-xs text-muted-foreground">
                Root Mean Square Error
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Data Points
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {combinedData.length}
              </div>
              <p className="text-xs text-muted-foreground">
                {viewMode === 'site' ? 'Daily aggregates' : 'Individual measurements'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Time Series Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Power Output Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={combinedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="actual_power" 
                      stroke="#2563eb" 
                      name="Actual Power"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="predicted_power" 
                      stroke="#dc2626" 
                      name="Predicted Power"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{ r: 3 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Scatter Plot */}
          <Card>
            <CardHeader>
              <CardTitle>Actual vs Predicted Power</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <Scatter data={combinedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      type="number" 
                      dataKey="actual_power" 
                      name="Actual Power"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="predicted_power" 
                      name="Predicted Power"
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip 
                      cursor={{ strokeDasharray: '3 3' }}
                      formatter={(value, name) => [value, name]}
                    />
                    <Scatter 
                      name="Power Comparison" 
                      data={combinedData.map(d => ({ 
                        actual_power: d.actual_power, 
                        predicted_power: d.predicted_power 
                      }))} 
                      fill="#2563eb"
                    />
                    {/* Perfect prediction line */}
                    <Line
                      type="linear"
                      dataKey="actual_power"
                      stroke="#6b7280"
                      strokeDasharray="2 2"
                      dot={false}
                      name="Perfect Prediction"
                    />
                  </Scatter>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {viewMode === 'skids' && (
          <div className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Skid-Level Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={combinedData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="skid_id" 
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="actual_power" fill="#2563eb" name="Actual Power" />
                      <Bar dataKey="predicted_power" fill="#dc2626" name="Predicted Power" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}