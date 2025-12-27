-- Simple test query
SELECT TOP 5
    s.student_code,
    u.full_name,
    u.email,
    sbv.balance_amount
FROM student_balance_view sbv
JOIN student s ON sbv.student_id = s.student_id
JOIN [user] u ON s.user_id = u.user_id
ORDER BY sbv.balance_amount DESC;

