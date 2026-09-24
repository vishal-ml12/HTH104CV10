-- Multi-Waste-Stream Contamination & Recycling Yield Optimizer
-- Phase 2 MySQL Database Schema: Multi-Stream Contamination Analysis & Yield Optimization

CREATE DATABASE IF NOT EXISTS waste_optimizer;
USE waste_optimizer;

CREATE TABLE IF NOT EXISTS waste_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE,
    material VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    contamination_level VARCHAR(50) NOT NULL,
    contamination_percentage FLOAT NOT NULL,
    quality_score FLOAT NOT NULL,
    recycling_yield FLOAT NOT NULL,
    recommendation VARCHAR(255) NOT NULL,
    recommendation_reason VARCHAR(500) NULL,
    processing_route VARCHAR(64) NULL,
    input_mass_kg FLOAT NOT NULL DEFAULT 100.0,
    recoverable_mass_kg FLOAT NULL,
    waste_loss_kg FLOAT NULL,
    total_objects INT NOT NULL DEFAULT 1,
    plastic_count INT NOT NULL DEFAULT 0,
    glass_count INT NOT NULL DEFAULT 0,
    metal_count INT NOT NULL DEFAULT 0,
    paper_count INT NOT NULL DEFAULT 0,
    organic_count INT NOT NULL DEFAULT 0,
    review_count INT NOT NULL DEFAULT 0,
    mode VARCHAR(30) NOT NULL DEFAULT 'REAL_YOLO',
    image_name VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_material (material),
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS detected_objects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_id INT NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    object_id VARCHAR(50) NOT NULL,
    material VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    box_x FLOAT NOT NULL,
    box_y FLOAT NOT NULL,
    box_width FLOAT NOT NULL,
    box_height FLOAT NOT NULL,
    stream VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'sorted',
    reviewed_material VARCHAR(50) NULL,
    contamination_score FLOAT NOT NULL DEFAULT 0.0,
    contamination_category VARCHAR(64) NOT NULL DEFAULT 'none',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_analysis_id (analysis_id),
    INDEX idx_session_id (session_id),
    INDEX idx_stream (stream),
    INDEX idx_status (status),
    CONSTRAINT fk_detected_analysis FOREIGN KEY (analysis_id) REFERENCES waste_analysis(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stream_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_id INT NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    stream_name VARCHAR(50) NOT NULL,
    item_count INT NOT NULL DEFAULT 0,
    stream_share_pct FLOAT NOT NULL DEFAULT 0.0,
    contamination_category VARCHAR(64) NOT NULL DEFAULT 'none',
    contamination_level VARCHAR(30) NOT NULL DEFAULT 'low',
    contamination_percentage FLOAT NOT NULL DEFAULT 0.0,
    quality_score FLOAT NOT NULL DEFAULT 0.0,
    estimated_yield FLOAT NOT NULL DEFAULT 0.0,
    yield_loss_handling FLOAT NOT NULL DEFAULT 0.0,
    yield_loss_contamination FLOAT NOT NULL DEFAULT 0.0,
    recoverable_mass_kg FLOAT NOT NULL DEFAULT 0.0,
    waste_loss_kg FLOAT NOT NULL DEFAULT 0.0,
    processing_route VARCHAR(64) NOT NULL DEFAULT 'DIRECT_RECYCLING',
    recommendation VARCHAR(255) NOT NULL,
    recommendation_reason VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stream_analysis_id (analysis_id),
    INDEX idx_stream_session_id (session_id),
    INDEX idx_stream_name (stream_name),
    CONSTRAINT fk_stream_analysis FOREIGN KEY (analysis_id) REFERENCES waste_analysis(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
