import { SitesResponse, SitePerformanceResponse, SkidsResponse } from "@/types/site";

// Mock data for demonstration when API is unavailable
export const mockSitesData: SitesResponse = {
  sites: [
    {
      site_id: "SITE001",
      site_name: "Solar Farm Alpha",
      location: "Arizona, USA",
      capacity_kw: 5000,
      installation_date: "2023-01-15",
      status: "active",
      connectivity_status: "connected"
    },
    {
      site_id: "SITE002",
      site_name: "Solar Farm Beta",
      location: "California, USA",
      capacity_kw: 3500,
      installation_date: "2023-03-20",
      status: "active",
      connectivity_status: "connected"
    },
    {
      site_id: "ASMB2",
      site_name: "Desert Solar Station",
      location: "Nevada, USA",
      capacity_kw: 7500,
      installation_date: "2022-11-10",
      status: "active",
      connectivity_status: "connected"
    },
    {
      site_id: "SITE003",
      site_name: "Coastal Solar Array",
      location: "Texas, USA",
      capacity_kw: 4200,
      installation_date: "2023-06-05",
      status: "active",
      connectivity_status: "disconnected"
    }
  ],
  total_count: 4
};

// Generate mock performance data
function generateMockPerformanceData(siteId: string): SitePerformanceResponse {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 30);
  
  const dataPoints = [];
  for (let i = 0; i < 30; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    // Generate realistic power values based on time of day
    for (let hour = 6; hour < 18; hour++) {
      const timestamp = new Date(date);
      timestamp.setHours(hour, 0, 0, 0);
      
      // Bell curve for solar production
      const peakHour = 12;
      const hourDiff = Math.abs(hour - peakHour);
      const basePower = 3000 * (1 - hourDiff / 6);
      
      const actualPower = basePower * (0.9 + Math.random() * 0.2);
      const expectedPower = basePower * 1.05;
      
      dataPoints.push({
        timestamp: timestamp.toISOString(),
        site_id: siteId,
        poa_irradiance: 800 * (1 - hourDiff / 6),
        actual_power: Math.max(0, actualPower),
        expected_power: Math.max(0, expectedPower),
        inverter_availability: 1.0,
        site_name: mockSitesData.sites.find(s => s.site_id === siteId)?.site_name || null,
        date: timestamp.toISOString().split('T')[0],
        predicted_power: Math.max(0, expectedPower),
        skid_id: `${siteId}_SKID001`
      });
    }
  }
  
  // Calculate metrics
  const actualValues = dataPoints.map(d => d.actual_power);
  const expectedValues = dataPoints.map(d => d.expected_power);
  
  const rmse = Math.sqrt(
    actualValues.reduce((sum, actual, i) => {
      const diff = actual - expectedValues[i];
      return sum + diff * diff;
    }, 0) / actualValues.length
  );
  
  const actualMean = actualValues.reduce((sum, val) => sum + val, 0) / actualValues.length;
  const totalSS = actualValues.reduce((sum, val) => {
    const diff = val - actualMean;
    return sum + diff * diff;
  }, 0);
  
  const residualSS = actualValues.reduce((sum, actual, i) => {
    const diff = actual - expectedValues[i];
    return sum + diff * diff;
  }, 0);
  
  const rSquared = totalSS === 0 ? 0 : 1 - (residualSS / totalSS);
  
  return {
    site_id: siteId,
    site_name: mockSitesData.sites.find(s => s.site_id === siteId)?.site_name,
    data_points: dataPoints,
    summary: {
      data_point_count: dataPoints.length,
      start_date: dataPoints[0].timestamp,
      end_date: dataPoints[dataPoints.length - 1].timestamp,
      avg_actual_power: actualMean,
      avg_expected_power: expectedValues.reduce((sum, val) => sum + val, 0) / expectedValues.length,
      total_actual_energy: actualValues.reduce((sum, val) => sum + val, 0),
      total_expected_energy: expectedValues.reduce((sum, val) => sum + val, 0),
      performance_ratio: 0.95
    },
    rmse: rmse,
    r_squared: rSquared
  };
}

export const mockSitePerformance = {
  getSitePerformance: (siteId: string): SitePerformanceResponse => {
    return generateMockPerformanceData(siteId);
  }
};

export const mockSkidsData: SkidsResponse = {
  site_id: "SITE001",
  skids: [
    {
      skid_id: "SKID001",
      skid_name: "Skid Unit 1",
      avg_actual_power: 1200,
      avg_expected_power: 1250,
      deviation_percentage: -4.0,
      data_point_count: 720
    },
    {
      skid_id: "SKID002",
      skid_name: "Skid Unit 2",
      avg_actual_power: 1150,
      avg_expected_power: 1250,
      deviation_percentage: -8.0,
      data_point_count: 720
    }
  ],
  total_count: 2
};