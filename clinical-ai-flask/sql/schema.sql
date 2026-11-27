-- ============================================================
-- CLINICAL AI SUITE - PATIENT INTAKE SCHEMA
-- COMP231 - Software Development Project I (Group 1)
-- Subsystem: Patient Experience & Intake Workflows
-- Module Owner: Joel
-- ============================================================
CREATE DATABASE scribeflow_db;
CREATE DATABASE IF NOT EXISTS scribeflow_db;
USE scribeflow_db;

-- Store patient demographic information
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    sex VARCHAR(30),
    phone VARCHAR(30),
    email VARCHAR(255),
    address VARCHAR(255),
    emergency_contact_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store clinical intake information and lifecycle status
CREATE TABLE IF NOT EXISTS patient_intakes (
    intake_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    reason_for_visit TEXT NOT NULL,
    symptoms TEXT,
    allergies TEXT,
    medications TEXT,
    intake_status ENUM(
        'Pending',
        'In Progress',
        'Completed'
    ) NOT NULL DEFAULT 'Pending',
    intake_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_intake_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    clinician VARCHAR(100) NOT NULL,
    datetime VARCHAR(50) NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'scheduled'
);

CREATE INDEX idx_patient_name
ON patients (last_name, first_name);

CREATE INDEX idx_intake_status
ON patient_intakes (intake_status);
