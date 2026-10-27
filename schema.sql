CREATE DATABASE IF NOT EXISTS road_accident_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE road_accident_db;

CREATE TABLE IF NOT EXISTS locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(120) NOT NULL,
    road_name VARCHAR(180) NULL,
    UNIQUE KEY uq_location (region, road_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS accidents (
    accident_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    accident_datetime DATETIME NOT NULL,
    location_id INT NOT NULL,
    vehicle_type VARCHAR(80) NOT NULL,
    severity ENUM('Minor', 'Serious', 'Fatal', 'Unknown') NOT NULL,
    weather VARCHAR(80) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_accidents_location
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_accident_datetime (accident_datetime),
    INDEX idx_severity (severity),
    INDEX idx_vehicle_type (vehicle_type)
) ENGINE=InnoDB;
