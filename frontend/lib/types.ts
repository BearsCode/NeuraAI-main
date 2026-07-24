export interface UserPublic {
  user_id: string;
  email: string;
  full_name: string;
  phone: string | null;
  company_name: string | null;
  role: string;
  admin_role: string | null;
  is_active: boolean;
}

export interface ProfileResponse extends UserPublic {
  referral_code: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
  user: UserPublic;
}

export interface ProjectSummaryResponse {
  project_id: string;
  company_name: string;
  industry: string;
  city: string;
  strategy_status: string;
}

export interface ProjectResponse {
  project_id: string;
  owner_user_id: string;
  company_name: string;
  business_description: string;
  city: string;
  industry: string;
  services: string[];
  website: string | null;
  phone: string | null;
  email: string | null;
  social_links: string[];
  target_audience: string;
  competitors: string[];
  business_features: string[];
  strategy_status: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardMetric {
  label: string;
  value: string | number;
  delta: string | null;
}

export interface DashboardCalendarItem {
  publication_id: string;
  platform: string;
  scheduled_at: string;
  status: string;
}

export interface DashboardResponse {
  project_id: string;
  metrics: DashboardMetric[];
  ai_recommendations: string[];
  content_calendar: DashboardCalendarItem[];
  strategy_state: string;
}

export interface StrategyResponse {
  project_id: string;
  positioning: string;
  content_pillars: string[];
  channels: string[];
  publishing_frequency: string;
}

export interface AIAnalysisResponse {
  project_id: string;
  business_analysis: string[];
  market_analysis: string[];
  competitor_analysis: string[];
}

export interface AIRecommendationResponse {
  project_id: string;
  recommendations: string[];
  optimization_mode: string;
}

export interface PlannedContentItem {
  content_item_id: string;
  date: string;
  time: string;
  platform: string;
  content_type: string;
  status: string;
  text: string;
  image_url: string | null;
  video_url: string | null;
}

export interface ContentPlanResponse {
  plan_id: string;
  project_id: string;
  period_days: number;
  source_mode: string;
  status: string;
  items: PlannedContentItem[];
}

export interface ProjectOverviewResponse {
  project: ProjectResponse;
  dashboard: DashboardResponse;
  strategy: StrategyResponse | null;
  analysis: AIAnalysisResponse | null;
  recommendations: AIRecommendationResponse | null;
  contentPlan: ContentPlanResponse;
}

export interface BusinessOnboardingPayload {
  company_name: string;
  business_description: string;
  city: string;
  industry: string;
  services: string[];
  website: string | null;
  phone: string | null;
  email: string | null;
  social_links: string[];
  target_audience: string;
  competitors: string[];
  business_features: string[];
}

export interface RegistrationAcceptedResponse {
  message: string;
  email: string;
  verification_required: boolean;
  verification_ttl_seconds: number;
  debug_code: string | null;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone?: string | null;
  company_name?: string | null;
  referral_code?: string | null;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ContentPlanGeneratePayload {
  period_days?: number;
  source_mode?: string;
  platforms?: string[];
  content_types?: string[];
}

// ── Additional types used across workspace pages ──

export interface SocialAccount {
  id: string;
  platform: string;
  account_identifier: string;
  status: string;
  settings?: Record<string, unknown>;
}

export interface PublishedPost {
  publication_id: string;
  planned_post_id?: string | null;
  platform: string;
  status: string;
  scheduled_at: string;
  published_at?: string | null;
  platform_post_id?: string | null;
}

export interface AnalyticsSummary {
  followers: number;
  impressions: number;
  likes: number;
  comments: number;
  saves: number;
  ctr: number;
  er: number;
}

export interface MvpContentPlanItem {
  content_item_id: string;
  platform: string;
  content_type: string;
  publish_at: string;
  status: string;
  text: string;
}

export interface MvpContentPlanResponse {
  plan_id: string;
  project_id: string;
  period_days: number;
  source_mode: string;
  status: string;
  items: MvpContentPlanItem[];
}

export interface MvpStrategyResponse {
  strategy_id: string | null;
  status: string;
  market_analysis: string[];
  competitor_analysis: string[];
  strategy_plan: Record<string, unknown>;
  content_strategy: Record<string, unknown>;
}

export interface PartnerDashboardData {
  referral_link: string;
  referral_code: string;
  total_referrals: number;
  successful_payments_count: number;
  total_commission: number;
  available_balance: number;
  commission_rate: number;
}

export interface UpdateProfilePayload {
  full_name: string;
  phone?: string | null;
  company_name?: string | null;
}

export interface DashboardData {
  user: ProfileResponse | null;
  projects: ProjectSummaryResponse[];
  analytics: AnalyticsSummary | null;
  strategy: MvpStrategyResponse | null;
  socials: SocialAccount[];
  contentPlan: MvpContentPlanResponse | null;
  publications: PublishedPost[];
  recommendations: Record<string, unknown>[];
}
