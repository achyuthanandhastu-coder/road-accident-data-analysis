import mysql.connector
from mysql.connector import Error
from config import Config


def get_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        use_unicode=True,
    )


def init_db():
    """Create the database and tables if they do not exist."""
    server_conn = mysql.connector.connect(
        host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
        charset="utf8mb4", use_unicode=True
    )
    try:
        cur = server_conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.close()
    finally:
        server_conn.close()

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                location_id INT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(120) NOT NULL,
                road_name VARCHAR(180) NULL,
                UNIQUE KEY uq_location (region, road_name)
            ) ENGINE=InnoDB
        """)
        cur.execute("""
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
            ) ENGINE=InnoDB
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()
