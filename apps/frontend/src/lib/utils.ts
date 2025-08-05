import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { PerformanceDataPoint } from "@/types/site"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function calculateRMSE(dataPoints: PerformanceDataPoint[]): number {
  if (dataPoints.length === 0) return 0;
  
  const sumSquaredErrors = dataPoints.reduce((sum, point) => {
    // Convert kW to MW for calculation
    const actualPowerMW = point.actual_power / 1000;
    const expectedPowerMW = point.expected_power / 1000;
    const error = actualPowerMW - expectedPowerMW;
    return sum + (error * error);
  }, 0);
  
  return Math.sqrt(sumSquaredErrors / dataPoints.length);
}

export function calculateRSquared(dataPoints: PerformanceDataPoint[]): number {
  if (dataPoints.length === 0) return 0;
  
  // Convert kW to MW for calculation
  const actualPowersMW = dataPoints.map(point => point.actual_power / 1000);
  const expectedPowersMW = dataPoints.map(point => point.expected_power / 1000);
  
  const actualMean = actualPowersMW.reduce((sum, power) => sum + power, 0) / actualPowersMW.length;
  
  const totalSumSquares = actualPowersMW.reduce((sum, power) => {
    const diff = power - actualMean;
    return sum + (diff * diff);
  }, 0);
  
  const residualSumSquares = actualPowersMW.reduce((sum, actualPower, index) => {
    const diff = actualPower - expectedPowersMW[index];
    return sum + (diff * diff);
  }, 0);
  
  if (totalSumSquares === 0) return 0;
  
  return 1 - (residualSumSquares / totalSumSquares);
}
