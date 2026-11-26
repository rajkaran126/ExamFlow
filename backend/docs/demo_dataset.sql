-- EXAMFLOW Seed Data for PS-072 Demonstration
INSERT INTO roles (id, name, description, created_at, updated_at) VALUES 
('a0000000-0000-0000-0000-000000000001', 'ADMIN', 'Super administrator and exam controller', NOW(), NOW()),
('a0000000-0000-0000-0000-000000000002', 'EXAMINER', 'Subject matter expert and evaluator', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

INSERT INTO users (id, email, hashed_password, name, role_type, is_active, created_at, updated_at) VALUES
('b0000000-0000-0000-0000-000000000001', 'admin@examflow.io', '$2b$12$eDx..fakehashedpass', 'Chief Examiner', 'ADMIN', true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

INSERT INTO examinations (id, code, name, description, duration_minutes, total_marks, passing_marks, status, negative_marking_enabled, sectional_cutoffs_enabled, normalisation_enabled, created_at, updated_at) VALUES
('c0000000-0000-0000-0000-000000000001', 'NERE-2024', 'PS-072 National Engineering Recruitment Exam', 'Exam with negative marking and multi-shift normalisation', 120, 100.00, 40.00, 'COMPLETED', true, true, true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
