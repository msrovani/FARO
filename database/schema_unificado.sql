-- ============================================================================
-- F.A.R.O. - Schema Unificado para Stack Atual
-- Versão: 1.0 (PostgreSQL + PostGIS + TimescaleDB + Citus)
-- Data: 2026-04-17
-- Gerado manualmente a partir de migrations Alembic e modelos SQLAlchemy
-- ============================================================================
-- NOTA: Este SQL deve ser executado em PostgreSQL com as seguintes extensões:
-- - PostGIS (geoespacial)
-- - TimescaleDB (time-series)
-- - Citus (clustering horizontal)
-- ============================================================================

-- 1. Extensões Necessárias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS citus;

-- 2. ENUMs (criados antes das tabelas)
CREATE TYPE userrole AS ENUM ('field_agent', 'intelligence', 'supervisor', 'admin');
CREATE TYPE agencytype AS ENUM ('local', 'regional', 'central');
CREATE TYPE unittype AS ENUM ('urban', 'highway', 'special');
CREATE TYPE streetnumberingdirection AS ENUM ('crescente', 'decrescente');
CREATE TYPE suspicionlevel AS ENUM ('low', 'medium', 'high');
CREATE TYPE urgencylevel AS ENUM ('monitor', 'intelligence', 'approach');
CREATE TYPE suspicionreason AS ENUM ('stolen_vehicle', 'suspicious_behavior', 'wanted_plate', 'unusual_hours', 'known_associate', 'drug_trafficking', 'weapons', 'gang_activity', 'other');
CREATE TYPE reviewstatus AS ENUM ('pending', 'confirmed', 'discarded', 'monitoring');
CREATE TYPE alerttype AS ENUM ('instant', 'pattern', 'recurrence', 'correlation');
CREATE TYPE alertseverity AS ENUM ('info', 'warning', 'critical');
CREATE TYPE syncstatus AS ENUM ('pending', 'syncing', 'completed', 'failed');
CREATE TYPE watchliststatus AS ENUM ('active', 'suspended', 'expired', 'closed');
CREATE TYPE watchlistcategory AS ENUM ('suspect_vehicle', 'monitored_vehicle', 'case_related', 'possible_clone', 'partial_plate', 'visual_only');
CREATE TYPE algorithmtype AS ENUM ('watchlist', 'impossible_travel', 'route_anomaly', 'sensitive_zone_recurrence', 'convoy', 'roaming', 'composite_score');
CREATE TYPE algorithmdecision AS ENUM ('no_match', 'weak_match', 'relevant_match', 'critical_match', 'impossible', 'highly_improbable', 'anomalous', 'discarded', 'normal', 'slight_deviation', 'relevant_anomaly', 'strong_anomaly', 'low_recurrence', 'medium_recurrence', 'relevant_recurrence', 'monitoring_recommended', 'casual', 'repeated', 'probable_convoy', 'strong_convoy', 'normal_circulation', 'light_roaming', 'relevant_roaming', 'likely_loitering', 'informative', 'monitor', 'relevant', 'high_risk', 'critical');
CREATE TYPE algorithmrunstatus AS ENUM ('pending', 'completed', 'failed');
CREATE TYPE casestatus AS ENUM ('open', 'monitoring', 'escalated', 'closed');
CREATE TYPE caselinktype AS ENUM ('observation', 'watchlist', 'score', 'occurrence', 'vehicle');
CREATE TYPE analystreviewstatus AS ENUM ('draft', 'final', 'rectified', 'supervisor_review');
CREATE TYPE analystconclusion AS ENUM ('improcedente', 'fraca', 'moderada', 'relevante', 'critica');
CREATE TYPE analystdecision AS ENUM ('discarded', 'in_analysis', 'confirmed_monitoring', 'confirmed_approach', 'linked_to_case', 'escalated');
CREATE TYPE crimetype AS ENUM ('drug_trafficking', 'contraband', 'escape', 'weapons_trafficking', 'kidnapping', 'car_theft', 'stolen_vehicle', 'gang_activity', 'human_trafficking', 'money_laundering', 'other');
CREATE TYPE routedirection AS ENUM ('inbound', 'outbound', 'bidirectional');
CREATE TYPE risklevel AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE batransmissionstatusenum AS ENUM ('pending', 'queued', 'transmitted', 'rejected', 'error', 'not_sent');

-- 3. Tabelas (em ordem de dependência)

-- agency
CREATE TABLE agency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    type agencytype NOT NULL DEFAULT 'local',
    parent_agency_id UUID REFERENCES agency(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_agency_name ON agency(name);
CREATE INDEX ix_agency_code ON agency(code);
CREATE INDEX ix_agency_parent_agency_id ON agency(parent_agency_id);

-- user
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf VARCHAR(11) UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    badge_number VARCHAR(50) UNIQUE,
    role userrole NOT NULL DEFAULT 'field_agent',
    agency_id UUID NOT NULL REFERENCES agency(id),
    unit_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    is_on_duty BOOLEAN NOT NULL DEFAULT false,
    service_expires_at TIMESTAMP WITH TIME ZONE,
    last_known_location GEOMETRY(POINT, 4326),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_user_cpf ON "user"(cpf);
CREATE INDEX ix_user_email ON "user"(email);
CREATE INDEX ix_user_badge_number ON "user"(badge_number);
CREATE INDEX ix_user_agency_id ON "user"(agency_id);
CREATE INDEX ix_user_role_active ON "user"(role, is_active);

-- unit
CREATE TABLE unit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    jurisdiction VARCHAR(255),
    unit_type unittype NOT NULL DEFAULT 'urban',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT uq_unit_agency_code UNIQUE (agency_id, code)
);

CREATE INDEX ix_unit_agency_id ON unit(agency_id);
CREATE INDEX ix_unit_code ON unit(code);

-- device
CREATE TABLE device (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id),
    agency_id UUID NOT NULL REFERENCES agency(id),
    device_id VARCHAR(255) NOT NULL,
    device_model VARCHAR(255) NOT NULL,
    os_version VARCHAR(100) NOT NULL,
    app_version VARCHAR(50) NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    last_justification TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT uq_device_user_device_id UNIQUE (user_id, device_id)
);

CREATE INDEX ix_device_user_id ON device(user_id);
CREATE INDEX ix_device_agency_id ON device(agency_id);
CREATE INDEX ix_device_device_id ON device(device_id);

-- agentlocationlog
CREATE TABLE agentlocationlog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES "user"(id),
    location GEOMETRY(POINT, 4326) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    connectivity_status VARCHAR(20),
    battery_level FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_agent_location_time ON agentlocationlog(agent_id, recorded_at);

-- vehicleobservation
CREATE TABLE vehicleobservation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(255) UNIQUE,
    agent_id UUID NOT NULL REFERENCES "user"(id),
    agency_id UUID NOT NULL REFERENCES agency(id),
    device_id UUID NOT NULL REFERENCES device(id),
    plate_number VARCHAR(20) NOT NULL,
    plate_state VARCHAR(10),
    plate_country VARCHAR(10) NOT NULL DEFAULT 'BR',
    observed_at_local TIMESTAMP WITH TIME ZONE NOT NULL,
    observed_at_server TIMESTAMP WITH TIME ZONE,
    location GEOMETRY(POINT, 4326) NOT NULL,
    location_accuracy FLOAT,
    heading FLOAT,
    speed FLOAT,
    vehicle_color VARCHAR(50),
    vehicle_type VARCHAR(50),
    vehicle_model VARCHAR(100),
    vehicle_year INTEGER,
    sync_status syncstatus NOT NULL DEFAULT 'pending',
    sync_attempts INTEGER NOT NULL DEFAULT 0,
    sync_error TEXT,
    synced_at TIMESTAMP WITH TIME ZONE,
    connectivity_type VARCHAR(20),
    metadata_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_vehicleobservation_client_id ON vehicleobservation(client_id);
CREATE INDEX ix_vehicleobservation_agent_id ON vehicleobservation(agent_id);
CREATE INDEX ix_vehicleobservation_agency_id ON vehicleobservation(agency_id);
CREATE INDEX ix_vehicleobservation_device_id ON vehicleobservation(device_id);
CREATE INDEX ix_vehicleobservation_plate_number ON vehicleobservation(plate_number);
CREATE INDEX ix_vehicleobservation_observed_at_local ON vehicleobservation(observed_at_local);
CREATE INDEX ix_observation_plate_time ON vehicleobservation(plate_number, observed_at_local);
CREATE INDEX ix_observation_agency_plate_time ON vehicleobservation(agency_id, plate_number, observed_at_local);
CREATE INDEX ix_observation_agent_time ON vehicleobservation(agent_id, observed_at_local);
CREATE INDEX ix_observation_sync_status ON vehicleobservation(sync_status);

-- plateread
CREATE TABLE plateread (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    ocr_raw_text TEXT NOT NULL,
    ocr_confidence FLOAT NOT NULL,
    ocr_engine VARCHAR(50) NOT NULL,
    image_url VARCHAR(500),
    image_hash VARCHAR(64),
    image_width INTEGER,
    image_height INTEGER,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- suspicionreport
CREATE TABLE suspicionreport (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL UNIQUE REFERENCES vehicleobservation(id),
    reason suspicionreason NOT NULL,
    level suspicionlevel NOT NULL,
    urgency urgencylevel NOT NULL,
    notes TEXT,
    abordado BOOLEAN,
    nivel_abordagem INTEGER,
    ocorrencia_registrada BOOLEAN,
    texto_ocorrencia TEXT,
    street_direction streetnumberingdirection,
    image_url VARCHAR(500),
    image_hash VARCHAR(64),
    audio_url VARCHAR(500),
    audio_duration_seconds INTEGER,
    system_relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- alert
CREATE TABLE alert (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type alerttype NOT NULL,
    severity alertseverity NOT NULL,
    observation_id UUID REFERENCES vehicleobservation(id),
    suspicion_report_id UUID REFERENCES suspicionreport(id),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    triggered_by_rule_id UUID,
    triggered_manually_by UUID REFERENCES "user"(id),
    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by UUID REFERENCES "user"(id),
    context_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_alert_severity_type ON alert(severity, alert_type);
CREATE INDEX ix_alert_acknowledged ON alert(is_acknowledged);

-- alertrule
CREATE TABLE alertrule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    conditions JSONB NOT NULL,
    alert_type alerttype NOT NULL,
    severity alertseverity NOT NULL,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- analystgeofence
CREATE TABLE analystgeofence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id),
    agency_id UUID NOT NULL REFERENCES agency(id),
    name VARCHAR(255) NOT NULL,
    area GEOMETRY(POLYGON, 4326) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL REFERENCES "user"(id),
    trigger_count INTEGER DEFAULT 0,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_analyst_geofence_user ON analystgeofence(user_id);

-- intelligencereview
CREATE TABLE intelligencereview (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    reviewer_id UUID NOT NULL REFERENCES "user"(id),
    status reviewstatus NOT NULL,
    justification TEXT NOT NULL,
    reclassified_reason suspicionreason,
    reclassified_level suspicionlevel,
    reclassified_urgency urgencylevel,
    occurrence_number VARCHAR(50),
    occurrence_url VARCHAR(500),
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_intelligencereview_status ON intelligencereview(status);

-- feedbackevent
CREATE TABLE feedbackevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL UNIQUE REFERENCES intelligencereview(id),
    target_agent_id UUID NOT NULL REFERENCES "user"(id),
    feedback_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    recommended_action VARCHAR(255),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- watchlistentry
CREATE TABLE watchlistentry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID NOT NULL REFERENCES "user"(id),
    agency_id UUID NOT NULL REFERENCES agency(id),
    status watchliststatus NOT NULL DEFAULT 'active',
    category watchlistcategory NOT NULL,
    plate_number VARCHAR(20),
    plate_partial VARCHAR(20),
    vehicle_make VARCHAR(100),
    vehicle_model VARCHAR(100),
    vehicle_color VARCHAR(50),
    visual_traits TEXT,
    interest_reason TEXT NOT NULL,
    information_source VARCHAR(255),
    sensitivity_level VARCHAR(50) NOT NULL DEFAULT 'reserved',
    confidence_level VARCHAR(50),
    geographic_scope VARCHAR(255),
    active_time_window VARCHAR(255),
    priority INTEGER NOT NULL DEFAULT 50,
    recommended_action VARCHAR(255),
    silent_mode BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    review_due_at TIMESTAMP WITH TIME ZONE,
    metadata_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_watchlist_status_priority ON watchlistentry(agency_id, status, priority);
CREATE INDEX ix_watchlist_plate_status ON watchlistentry(agency_id, plate_number, status);
CREATE INDEX ix_watchlistentry_created_by ON watchlistentry(created_by);
CREATE INDEX ix_watchlistentry_agency_id ON watchlistentry(agency_id);
CREATE INDEX ix_watchlistentry_status ON watchlistentry(status);
CREATE INDEX ix_watchlistentry_category ON watchlistentry(category);
CREATE INDEX ix_watchlistentry_valid_until ON watchlistentry(valid_until);
CREATE INDEX ix_watchlistentry_review_due_at ON watchlistentry(review_due_at);

-- routepattern
CREATE TABLE routepattern (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    plate_number VARCHAR(20) NOT NULL,
    observation_count INTEGER NOT NULL,
    first_observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    centroid_location GEOMETRY(POINT, 4326) NOT NULL,
    bounding_box GEOMETRY(POLYGON, 4326) NOT NULL,
    corridor GEOMETRY(LINESTRING, 4326),
    primary_corridor_name VARCHAR(255),
    predominant_direction FLOAT,
    recurrence_score FLOAT NOT NULL,
    pattern_strength VARCHAR(20) NOT NULL,
    common_hours INTEGER[],
    common_days INTEGER[],
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    analysis_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_route_pattern_plate ON routepattern(agency_id, plate_number);
CREATE INDEX ix_route_pattern_strength ON routepattern(pattern_strength);

-- auditlog
CREATE TABLE auditlog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "user"(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    justification TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_audit_resource ON auditlog(resource_type, resource_id);
CREATE INDEX ix_audit_action_time ON auditlog(action, created_at);

-- syncqueue
CREATE TABLE syncqueue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_local_id VARCHAR(255) NOT NULL,
    entity_server_id UUID,
    operation VARCHAR(20) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    status syncstatus NOT NULL DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    created_at_local TIMESTAMP WITH TIME ZONE NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_syncqueue_status_attempts ON syncqueue(status, attempt_count);
CREATE INDEX ix_syncqueue_client_device ON syncqueue(client_id, device_id);

-- externalquery
CREATE TABLE externalquery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID REFERENCES vehicleobservation(id),
    query_type VARCHAR(50) NOT NULL,
    queried_value VARCHAR(255) NOT NULL,
    system_name VARCHAR(100) NOT NULL,
    request_payload JSONB,
    response_status VARCHAR(50) NOT NULL,
    response_data JSONB,
    response_hash VARCHAR(64),
    queried_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    response_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- asset
CREATE TABLE asset (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_type VARCHAR(50) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL UNIQUE,
    storage_bucket VARCHAR(100) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    uploaded_by UUID NOT NULL REFERENCES "user"(id),
    uploaded_from_device UUID REFERENCES device(id),
    width INTEGER,
    height INTEGER,
    duration_seconds INTEGER,
    related_observation_id UUID REFERENCES vehicleobservation(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_asset_type_observation ON asset(asset_type, related_observation_id);

-- watchlistrule
CREATE TABLE watchlistrule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_entry_id UUID NOT NULL REFERENCES watchlistentry(id),
    name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'moderate',
    target_scope VARCHAR(50) NOT NULL DEFAULT 'intelligence_only',
    geographic_scope VARCHAR(255),
    time_window VARCHAR(255),
    conditions_json JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_watchlistrule_watchlist_entry_id ON watchlistrule(watchlist_entry_id);

-- watchlisthit
CREATE TABLE watchlisthit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    watchlist_entry_id UUID NOT NULL REFERENCES watchlistentry(id),
    decision algorithmdecision NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_watchlisthit_observation_watchlist ON watchlisthit(observation_id, watchlist_entry_id);
CREATE INDEX ix_watchlisthit_observation_id ON watchlisthit(observation_id);
CREATE INDEX ix_watchlisthit_watchlist_entry_id ON watchlisthit(watchlist_entry_id);

-- routeregionofinterest
CREATE TABLE routeregionofinterest (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    name VARCHAR(255) NOT NULL,
    region_type VARCHAR(100) NOT NULL,
    municipality VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_routeregionofinterest_agency_id ON routeregionofinterest(agency_id);
CREATE INDEX ix_routeregionofinterest_name ON routeregionofinterest(name);

-- sensitiveassetzone
CREATE TABLE sensitiveassetzone (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(100) NOT NULL,
    municipality VARCHAR(100),
    severity VARCHAR(50) NOT NULL DEFAULT 'high',
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    radius_meters FLOAT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_sensitiveassetzone_agency_id ON sensitiveassetzone(agency_id);
CREATE INDEX ix_sensitiveassetzone_name ON sensitiveassetzone(name);

-- impossibletravelevent
CREATE TABLE impossibletravelevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    previous_observation_id UUID REFERENCES vehicleobservation(id),
    plate_number VARCHAR(20) NOT NULL,
    decision algorithmdecision NOT NULL,
    distance_km FLOAT NOT NULL,
    travel_time_minutes FLOAT NOT NULL,
    plausible_time_minutes FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_impossibletravelevent_observation_id ON impossibletravelevent(observation_id);
CREATE INDEX ix_impossibletravelevent_plate_number ON impossibletravelevent(plate_number);

-- routeanomalyevent
CREATE TABLE routeanomalyevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    plate_number VARCHAR(20) NOT NULL,
    region_from_id UUID REFERENCES routeregionofinterest(id),
    region_to_id UUID REFERENCES routeregionofinterest(id),
    decision algorithmdecision NOT NULL,
    anomaly_score FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_routeanomalyevent_observation_id ON routeanomalyevent(observation_id);
CREATE INDEX ix_routeanomalyevent_plate_number ON routeanomalyevent(plate_number);

-- sensitiveassetrecurrenceevent
CREATE TABLE sensitiveassetrecurrenceevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    zone_id UUID NOT NULL REFERENCES sensitiveassetzone(id),
    plate_number VARCHAR(20) NOT NULL,
    recurrence_count INTEGER NOT NULL,
    decision algorithmdecision NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_sensitiveassetrecurrenceevent_observation_id ON sensitiveassetrecurrenceevent(observation_id);
CREATE INDEX ix_sensitiveassetrecurrenceevent_zone_id ON sensitiveassetrecurrenceevent(zone_id);
CREATE INDEX ix_sensitiveassetrecurrenceevent_plate_number ON sensitiveassetrecurrenceevent(plate_number);

-- convoyevent
CREATE TABLE convoyevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    primary_plate VARCHAR(20) NOT NULL,
    related_plate VARCHAR(20) NOT NULL,
    cooccurrence_count INTEGER NOT NULL,
    convoy_id UUID,
    convoy_size INTEGER,
    spatial_proximity_meters FLOAT,
    temporal_window_minutes INTEGER,
    route_similarity FLOAT,
    common_hours INTEGER[],
    common_days INTEGER[],
    decision algorithmdecision NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_convoyevent_observation_id ON convoyevent(observation_id);
CREATE INDEX ix_convoyevent_primary_plate ON convoyevent(primary_plate);
CREATE INDEX ix_convoyevent_related_plate ON convoyevent(related_plate);
CREATE INDEX ix_convoy_convoy_id ON convoyevent(convoy_id);
CREATE INDEX ix_convoy_primary_related ON convoyevent(primary_plate, related_plate);

-- roamingevent
CREATE TABLE roamingevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    plate_number VARCHAR(20) NOT NULL,
    area_label VARCHAR(255) NOT NULL,
    recurrence_count INTEGER NOT NULL,
    roaming_id UUID,
    area_geometry GEOMETRY(POLYGON, 4326),
    area_size_km2 FLOAT,
    average_stay_minutes FLOAT,
    total_observations INTEGER,
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    common_hours INTEGER[],
    common_days INTEGER[],
    zone_type VARCHAR(100),
    zone_risk_level VARCHAR(50),
    decision algorithmdecision NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_roamingevent_observation_id ON roamingevent(observation_id);
CREATE INDEX ix_roamingevent_plate_number ON roamingevent(plate_number);
CREATE INDEX ix_roaming_roaming_id ON roamingevent(roaming_id);
CREATE INDEX ix_roaming_plate_area ON roamingevent(plate_number, area_label);

-- suspiciousroute
CREATE TABLE suspiciousroute (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    name VARCHAR(255) NOT NULL,
    crime_type crimetype NOT NULL,
    direction routedirection NOT NULL,
    risk_level risklevel NOT NULL,
    route_geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    buffer_distance_meters FLOAT,
    active_from_hour INTEGER,
    active_to_hour INTEGER,
    active_days INTEGER[],
    justification TEXT,
    created_by UUID NOT NULL REFERENCES "user"(id),
    approved_by UUID REFERENCES "user"(id),
    approval_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_suspiciousroute_agency_id ON suspiciousroute(agency_id);
CREATE INDEX ix_suspiciousroute_name ON suspiciousroute(name);
CREATE INDEX ix_suspicious_route_agency_active ON suspiciousroute(agency_id, is_active);
CREATE INDEX ix_suspicious_route_crime_type ON suspiciousroute(crime_type);

-- suspicionscore
CREATE TABLE suspicionscore (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL UNIQUE REFERENCES vehicleobservation(id),
    plate_number VARCHAR(20) NOT NULL,
    final_score FLOAT NOT NULL,
    final_label algorithmdecision NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    false_positive_risk VARCHAR(50) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_suspicionscore_observation_id ON suspicionscore(observation_id);
CREATE INDEX ix_suspicionscore_plate_number ON suspicionscore(plate_number);

-- suspicionscorefactor
CREATE TABLE suspicionscorefactor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suspicion_score_id UUID NOT NULL REFERENCES suspicionscore(id),
    factor_name VARCHAR(255) NOT NULL,
    factor_source VARCHAR(100) NOT NULL,
    weight FLOAT NOT NULL,
    contribution FLOAT NOT NULL,
    explanation TEXT NOT NULL,
    direction VARCHAR(20) NOT NULL DEFAULT 'positive',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_suspicionscorefactor_suspicion_score_id ON suspicionscorefactor(suspicion_score_id);

-- intelligencecase
CREATE TABLE intelligencecase (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    created_by UUID NOT NULL REFERENCES "user"(id),
    title VARCHAR(255) NOT NULL,
    hypothesis TEXT,
    summary TEXT,
    status casestatus NOT NULL DEFAULT 'open',
    sensitivity_level VARCHAR(50) NOT NULL DEFAULT 'reserved',
    priority INTEGER NOT NULL DEFAULT 50,
    review_due_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_intelligencecase_agency_id ON intelligencecase(agency_id);
CREATE INDEX ix_intelligencecase_created_by ON intelligencecase(created_by);
CREATE INDEX ix_intelligencecase_title ON intelligencecase(title);
CREATE INDEX ix_intelligencecase_status ON intelligencecase(status);

-- caselink
CREATE TABLE caselink (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES intelligencecase(id),
    link_type caselinktype NOT NULL,
    linked_entity_id UUID NOT NULL,
    linked_label VARCHAR(255),
    created_by UUID NOT NULL REFERENCES "user"(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_caselink_case_id ON caselink(case_id);
CREATE INDEX ix_caselink_linked_entity_id ON caselink(linked_entity_id);

-- analystreview
CREATE TABLE analystreview (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL REFERENCES vehicleobservation(id),
    analyst_id UUID NOT NULL REFERENCES "user"(id),
    status analystreviewstatus NOT NULL DEFAULT 'draft',
    conclusion analystconclusion,
    decision analystdecision,
    source_quality VARCHAR(100),
    data_reliability VARCHAR(100),
    reinforcing_factors JSONB,
    weakening_factors JSONB,
    recommendation VARCHAR(255),
    justification TEXT NOT NULL DEFAULT '',
    sensitivity_level VARCHAR(50) NOT NULL DEFAULT 'reserved',
    review_due_at TIMESTAMP WITH TIME ZONE,
    linked_case_id UUID REFERENCES intelligencecase(id),
    linked_occurrence_ref VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_analystreview_observation_id ON analystreview(observation_id);
CREATE INDEX ix_analystreview_analyst_id ON analystreview(analyst_id);

-- analystreviewversion
CREATE TABLE analystreviewversion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analyst_review_id UUID NOT NULL REFERENCES analystreview(id),
    version_number INTEGER NOT NULL,
    changed_by UUID NOT NULL REFERENCES "user"(id),
    change_reason TEXT,
    snapshot_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_analystreviewversion_analyst_review_id ON analystreviewversion(analyst_review_id);

-- analystfeedbacktemplate
CREATE TABLE analystfeedbacktemplate (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    created_by UUID NOT NULL REFERENCES "user"(id),
    name VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    sensitivity_level VARCHAR(50) NOT NULL DEFAULT 'operational',
    body_template TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_analystfeedbacktemplate_agency_id ON analystfeedbacktemplate(agency_id);

-- analystfeedbackevent
CREATE TABLE analystfeedbackevent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agency(id),
    observation_id UUID REFERENCES vehicleobservation(id),
    analyst_id UUID NOT NULL REFERENCES "user"(id),
    target_user_id UUID REFERENCES "user"(id),
    target_team_label VARCHAR(255),
    feedback_type VARCHAR(50) NOT NULL,
    sensitivity_level VARCHAR(50) NOT NULL DEFAULT 'operational',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    template_id UUID REFERENCES analystfeedbacktemplate(id),
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_analystfeedbackevent_agency_id ON analystfeedbackevent(agency_id);
CREATE INDEX ix_analystfeedbackevent_observation_id ON analystfeedbackevent(observation_id);
CREATE INDEX ix_analystfeedbackevent_analyst_id ON analystfeedbackevent(analyst_id);

-- algorithmrun
CREATE TABLE algorithmrun (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_type algorithmtype NOT NULL,
    observation_id UUID REFERENCES vehicleobservation(id),
    run_scope VARCHAR(20) NOT NULL DEFAULT 'online',
    status algorithmrunstatus NOT NULL DEFAULT 'pending',
    payload_version VARCHAR(20) NOT NULL DEFAULT 'v1',
    input_payload JSONB,
    output_payload JSONB,
    executed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_algorithmrun_algorithm_type ON algorithmrun(algorithm_type);
CREATE INDEX ix_algorithmrun_observation_id ON algorithmrun(observation_id);

-- algorithmexplanation
CREATE TABLE algorithmexplanation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_run_id UUID NOT NULL REFERENCES algorithmrun(id),
    algorithm_type algorithmtype NOT NULL,
    decision algorithmdecision,
    confidence FLOAT,
    severity VARCHAR(50),
    explanation_text TEXT NOT NULL,
    false_positive_risk VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_algorithmexplanation_algorithm_run_id ON algorithmexplanation(algorithm_run_id);
CREATE INDEX ix_algorithmexplanation_algorithm_type ON algorithmexplanation(algorithm_type);

-- boletimatendimento
CREATE TABLE boletimatendimento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id UUID NOT NULL UNIQUE REFERENCES vehicleobservation(id),
    agent_id UUID NOT NULL REFERENCES "user"(id),
    agency_id UUID NOT NULL REFERENCES agency(id),
    plate_number VARCHAR(20) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    approach_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    payload_json JSONB NOT NULL,
    transmission_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    transmission_error TEXT,
    transmitted_at TIMESTAMP WITH TIME ZONE,
    external_protocol VARCHAR(100),
    batch_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_boletimatendimento_observation_id ON boletimatendimento(observation_id);
CREATE INDEX ix_boletimatendimento_agent_id ON boletimatendimento(agent_id);
CREATE INDEX ix_boletimatendimento_agency_id ON boletimatendimento(agency_id);
CREATE INDEX ix_boletimatendimento_plate_number ON boletimatendimento(plate_number);
CREATE INDEX ix_ba_status_created ON boletimatendimento(transmission_status, created_at);
CREATE INDEX ix_ba_agent_created ON boletimatendimento(agent_id, created_at);

-- 4. Índices Geoespaciais (GiST) - Migration 0002
CREATE INDEX IF NOT EXISTS ix_vehicleobservation_location_gist ON vehicleobservation USING GIST (location);
CREATE INDEX IF NOT EXISTS ix_routepattern_centroid_location_gist ON routepattern USING GIST (centroid_location);
CREATE INDEX IF NOT EXISTS ix_routepattern_bounding_box_gist ON routepattern USING GIST (bounding_box);
CREATE INDEX IF NOT EXISTS ix_routepattern_corridor_gist ON routepattern USING GIST (corridor);
CREATE INDEX IF NOT EXISTS ix_routeregionofinterest_geometry_gist ON routeregionofinterest USING GIST (geometry);
CREATE INDEX IF NOT EXISTS ix_sensitiveassetzone_geometry_gist ON sensitiveassetzone USING GIST (geometry);
CREATE INDEX IF NOT EXISTS ix_suspiciousroute_route_geometry ON suspiciousroute USING GIST (route_geometry);
CREATE INDEX IF NOT EXISTS ix_roaming_area_geometry ON roamingevent USING GIST (area_geometry);
CREATE INDEX IF NOT EXISTS ix_analystgeofence_area ON analystgeofence USING GIST (area);
CREATE INDEX IF NOT EXISTS ix_agentlocationlog_location ON agentlocationlog USING GIST (location);

-- 5. Índices Operacionais (B-Tree) - Migration 0002
CREATE INDEX IF NOT EXISTS ix_routeanomalyevent_plate_created_at ON routeanomalyevent (plate_number, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_convoyevent_primary_related_created_at ON convoyevent (primary_plate, related_plate, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_roamingevent_plate_created_at ON roamingevent (plate_number, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_sensitiveassetrecurrenceevent_plate_zone_created_at ON sensitiveassetrecurrenceevent (plate_number, zone_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_algorithmrun_type_scope_status_created_at ON algorithmrun (algorithm_type, run_scope, status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_algorithmexplanation_run_type ON algorithmexplanation (algorithm_run_id, algorithm_type);
CREATE INDEX IF NOT EXISTS ix_analystfeedbackevent_target_read_created_at ON analystfeedbackevent (target_user_id, read_at, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_auditlog_user_action_created_at ON auditlog (user_id, action, created_at DESC);

-- 6. BRIN Indexes - Migration 0007
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_vehicleobservation_observed_at_local_brin
ON vehicleobservation USING BRIN (observed_at_local)
WITH (pages_per_range = 128);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_vehicleobservation_created_at_brin
ON vehicleobservation USING BRIN (created_at)
WITH (pages_per_range = 128);

-- 7. Parallel Query Tuning - Migration 0008
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;
ALTER SYSTEM SET parallel_setup_cost = 1000;
ALTER SYSTEM SET parallel_tuple_cost = 0.1;
SELECT pg_reload_conf();

-- 8. Materialized Views - Migration 0009
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_hotspots AS
SELECT
    date_trunc('day', vo.observed_at_local) as observation_date,
    ST_ClusterWithin(
        ST_Collect(vo.location),
        500  -- cluster radius in meters
    ) as hotspot_clusters,
    COUNT(*) as observation_count,
    COUNT(DISTINCT vo.plate_number) as unique_plates
FROM vehicleobservation vo
WHERE vo.observed_at_local >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date_trunc('day', vo.observed_at_local)
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_daily_hotspots_date_idx
ON mv_daily_hotspots (observation_date);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_agency_hotspots AS
SELECT
    vo.agency_id,
    date_trunc('day', vo.observed_at_local) as observation_date,
    ST_ClusterWithin(
        ST_Collect(vo.location),
        500  -- cluster radius in meters
    ) as hotspot_clusters,
    COUNT(*) as observation_count,
    COUNT(DISTINCT vo.plate_number) as unique_plates
FROM vehicleobservation vo
WHERE vo.observed_at_local >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY vo.agency_id, date_trunc('day', vo.observed_at_local)
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_agency_hotspots_agency_date_idx
ON mv_agency_hotspots (agency_id, observation_date);

-- 9. TimescaleDB Hypertable - Migration 0010
SELECT create_hypertable(
    'vehicleobservation',
    'observed_at_local',
    if_not_exists => TRUE
);

-- Continuous Aggregate (TimescaleDB)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_observation_counts
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', observed_at_local) as bucket,
    agency_id,
    COUNT(*) as observation_count,
    COUNT(DISTINCT plate_number) as unique_plates
FROM vehicleobservation
GROUP BY bucket, agency_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('mv_daily_observation_counts',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour');

-- 10. Citus Distributed Tables - Migration 0011
SELECT create_distributed_table('vehicleobservation', 'agency_id');
SELECT create_distributed_table('convoyevent', 'agency_id');
SELECT create_distributed_table('impossibletravelevent', 'agency_id');
SELECT create_distributed_table('routeanomalyevent', 'agency_id');
SELECT create_distributed_table('sensitiveassetrecurrenceevent', 'agency_id');
SELECT create_distributed_table('roamingevent', 'agency_id');
SELECT create_distributed_table('suspicionscore', 'agency_id');
SELECT create_distributed_table('watchlisthit', 'agency_id');
SELECT create_reference_table('agency');
SELECT create_reference_table('user');

-- 11. Dados Iniciais - Bootstrap Agency
INSERT INTO agency (id, name, code, is_active, type)
VALUES ('11111111-1111-1111-1111-111111111111', 'Agencia Padrao FARO', 'FARO-DEFAULT', true, 'local')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- FIM DO SCHEMA UNIFICADO
-- ============================================================================
