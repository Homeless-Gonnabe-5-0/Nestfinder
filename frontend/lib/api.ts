// API client for NestFinder backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SearchRequest {
  budget_min: number;
  budget_max: number;
  work_address: string;
  bedrooms: number;
  priorities: string[];
  max_commute_minutes: number;
  transport_mode: string;
}

export interface Apartment {
  id: string;
  title: string;
  address: string;
  neighborhood: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft?: number;
  amenities: string[];
  pet_friendly: boolean;
  parking_included: boolean;
  laundry_type: string;
  image_url?: string;
  source_url?: string;
  lat?: number;
  lng?: number;
}

export interface CommuteAnalysis {
  apartment_id: string;
  transit_minutes?: number;
  driving_minutes?: number;
  biking_minutes?: number;
  walking_minutes?: number;
  best_mode: string;
  best_time: number;
  commute_score: number;
  summary: string;
}

export interface NeighborhoodAnalysis {
  apartment_id: string;
  neighborhood_name: string;
  safety_score: number;
  safety_rating: string;
  walkability_score: number;
  nightlife_score: number;
  quiet_score: number;
  grocery_nearby: string[];
  restaurants_nearby: number;
  parks_nearby: number;
  neighborhood_score: number;
  summary: string;
}

export interface BudgetAnalysis {
  apartment_id: string;
  monthly_rent: number;
  estimated_utilities: number;
  total_monthly: number;
  market_average: number;
  price_difference: number;
  price_difference_percent: number;
  price_per_sqft?: number;
  is_good_deal: boolean;
  budget_score: number;
  summary: string;
}

export interface Recommendation {
  rank: number;
  apartment: Apartment;
  commute: CommuteAnalysis;
  neighborhood: NeighborhoodAnalysis;
  budget: BudgetAnalysis;
  overall_score: number;
  headline: string;
  match_reasons: string[];
  concerns: string[];
}

export interface SearchResponse {
  search_id: string;
  total_found: number;
  recommendations: Recommendation[];
  search_params: SearchRequest;
  searched_at: string;
}

export async function searchApartments(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Search failed' }));
    throw new Error(error.detail || 'Search failed');
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  return response.json();
}

export async function getPriorities(): Promise<{ priorities: string[] }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/priorities`);
  return response.json();
}

export async function getNeighborhoods(): Promise<{ neighborhoods: string[] }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/neighborhoods`);
  return response.json();
}

export async function getTransportModes(): Promise<{ modes: string[] }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/transport-modes`);
  return response.json();
}
