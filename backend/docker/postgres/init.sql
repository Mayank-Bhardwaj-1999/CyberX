-- Initialize PostgreSQL database for analytics and rate limiting
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- API Analytics table
CREATE TABLE IF NOT EXISTS api_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    ip_address INET,
    user_agent TEXT,
    request_size INTEGER DEFAULT 0,
    response_size INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    worker_id VARCHAR(50)
);

-- Rate limiting table
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip_address INET NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_request TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ip_address, endpoint, window_start)
);

-- API Keys table for authenticated access
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    rate_limit INTEGER DEFAULT 1000,
    daily_limit INTEGER DEFAULT 10000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0
);

-- Error tracking table
CREATE TABLE IF NOT EXISTS api_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255) NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT,
    stack_trace TEXT,
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    worker_id VARCHAR(50)
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    worker_id VARCHAR(50)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_api_analytics_timestamp ON api_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_analytics_endpoint ON api_analytics(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_analytics_ip ON api_analytics(ip_address);
CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_endpoint ON rate_limits(ip_address, endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);
CREATE INDEX IF NOT EXISTS idx_api_errors_timestamp ON api_errors(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Create a user for the application
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'cybersec_user') THEN
        CREATE USER cybersec_user WITH PASSWORD 'secure_password_123';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE cybersec_analytics TO cybersec_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cybersec_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cybersec_user;
