import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { PerformanceDataPoint } from "@/types/site"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function calculateRMSE(dataPoints: PerformanceDataPoint[]): number;
export function calculateRMSE(actualValues: number[], predictedValues: number[]): number;
export function calculateRMSE(arg1: PerformanceDataPoint[] | number[], arg2?: number[]): number {
  if (Array.isArray(arg1) && arg1.length === 0) return 0;
  
  // Handle two different call signatures
  if (arg2 !== undefined) {
    // Called with two arrays of numbers
    const actualValues = arg1 as number[];
    const predictedValues = arg2;
    
    if (actualValues.length !== predictedValues.length || actualValues.length === 0) return 0;
    
    const sumSquaredErrors = actualValues.reduce((sum, actual, index) => {
      const error = actual - predictedValues[index];
      return sum + (error * error);
    }, 0);
    
    return Math.sqrt(sumSquaredErrors / actualValues.length);
  } else {
    // Called with array of PerformanceDataPoint
    const dataPoints = arg1 as PerformanceDataPoint[];
    
    const sumSquaredErrors = dataPoints.reduce((sum, point) => {
      // Convert kW to MW for calculation
      const actualPowerMW = point.actual_power / 1000;
      const expectedPowerMW = point.expected_power / 1000;
      const error = actualPowerMW - expectedPowerMW;
      return sum + (error * error);
    }, 0);
    
    return Math.sqrt(sumSquaredErrors / dataPoints.length);
  }
}

export function calculateRSquared(dataPoints: PerformanceDataPoint[]): number;
export function calculateRSquared(actualValues: number[], predictedValues: number[]): number;
export function calculateRSquared(arg1: PerformanceDataPoint[] | number[], arg2?: number[]): number {
  if (Array.isArray(arg1) && arg1.length === 0) return 0;
  
  let actualValues: number[];
  let predictedValues: number[];
  
  if (arg2 !== undefined) {
    // Called with two arrays of numbers
    actualValues = arg1 as number[];
    predictedValues = arg2;
  } else {
    // Called with array of PerformanceDataPoint
    const dataPoints = arg1 as PerformanceDataPoint[];
    // Convert kW to MW for calculation
    actualValues = dataPoints.map(point => point.actual_power / 1000);
    predictedValues = dataPoints.map(point => point.expected_power / 1000);
  }
  
  if (actualValues.length !== predictedValues.length || actualValues.length === 0) return 0;
  
  const actualMean = actualValues.reduce((sum, value) => sum + value, 0) / actualValues.length;
  
  const totalSumSquares = actualValues.reduce((sum, value) => {
    const diff = value - actualMean;
    return sum + (diff * diff);
  }, 0);
  
  const residualSumSquares = actualValues.reduce((sum, actualValue, index) => {
    const diff = actualValue - predictedValues[index];
    return sum + (diff * diff);
  }, 0);
  
  if (totalSumSquares === 0) return 0;
  
  return 1 - (residualSumSquares / totalSumSquares);
}
