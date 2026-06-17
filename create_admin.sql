-- SQL script to create superadmin user
-- Password: 061167@aB1
-- Password hash was generated with bcrypt using cost=12

INSERT INTO users (
    email,
    full_name,
    password_hash,
    role,
    is_active,
    is_verified,
    preferences,
    created_at
) VALUES (
    'hamka.suleiman@calmic.com.my',
    'Hamka Suleiman',
    '$2b$12$gF5VqL8UHo4k4VcM7r9jJ.uo4OhQKfzK4qL8G7m5H3n9Q8p7T6s5K',
    'admin',
    true,
    true,
    '{}',
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    role = 'admin',
    is_active = true,
    is_verified = true,
    password_hash = '$2b$12$gF5VqL8UHo4k4VcM7r9jJ.uo4OhQKfzK4qL8G7m5H3n9Q8p7T6s5K';
