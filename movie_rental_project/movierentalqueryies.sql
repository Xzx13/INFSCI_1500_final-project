USE movierental;

-- 1. SEARCH BY ACTOR
SELECT 
    m.title AS "Movie Title", 
    m.release_year AS "Year", 
    m.movie_rating AS "Rating", 
    ma.role_name AS "Character Name"
FROM movie m
JOIN movie_actor ma ON m.movie_id = ma.movie_id
JOIN actor a ON ma.actor_id = a.actor_id
WHERE a.actor_name LIKE '%Keanu Reeves%';

-- 2. SEARCH BY CATEGORY
SELECT 
    m.title AS "Movie Title", 
    m.description AS "Plot Summary", 
    c.category_name AS "Genre"
FROM movie m
JOIN movie_category mc ON m.movie_id = mc.movie_id
JOIN category c ON mc.category_id = c.category_id
WHERE c.category_name = 'Sci-Fi';

-- 3. CHECK AVAILABLE COPIES
SELECT 
    m.title AS "Movie Title", 
    COUNT(ic.copy_id) AS "Copies Available on Shelf"
FROM movie m
JOIN inventory_copy ic ON m.movie_id = ic.movie_id
WHERE ic.status = 'AVAILABLE'
GROUP BY m.title;

-- 4. SIMULATE RENTING A MOVIE
-- Action: Insert rental record and mark copy as RENTED
INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status)
VALUES (1, 1, NOW(), DATE_ADD(NOW(), INTERVAL 5 DAY), 'OPEN');

UPDATE inventory_copy
SET status = 'RENTED'
WHERE copy_id = 1;

-- VERIFY STEP 4: Transaction Receipt
SELECT 
    r.rental_id AS "Rental ID", 
    r.rental_date AS "Date Rented", 
    r.rental_status AS "Rental Status", 
    ic.copy_id AS "Copy ID", 
    ic.status AS "Current Shelf Status" 
FROM rental r
JOIN inventory_copy ic ON r.copy_id = ic.copy_id
WHERE r.copy_id = 1 
ORDER BY r.rental_id DESC 
LIMIT 1;

-- 5. SIMULATE RETURNING A MOVIE
-- Action: Close the rental and mark copy as AVAILABLE
UPDATE rental
SET return_date = NOW(), rental_status = 'RETURNED'
WHERE rental_id = 1;

UPDATE inventory_copy
SET status = 'AVAILABLE'
WHERE copy_id = 1;

-- VERIFY STEP 5: Return Receipt
SELECT 
    r.rental_id AS "Rental ID", 
    r.return_date AS "Date Returned", 
    r.rental_status AS "Status", 
    ic.status AS "Item Status" 
FROM rental r
JOIN inventory_copy ic ON r.copy_id = ic.copy_id
WHERE r.rental_id = 1;

-- 6. ADD STANDARD PAYMENT DATA
INSERT INTO payment (rental_id, amount, payment_date, payment_method)
VALUES (1, 4.99, NOW(), 'CARD');

INSERT INTO customer (first_name, last_name, email, phone, address, signup_date)
VALUES ('John', 'Doe', 'john.doe@pitt.edu', '412-555-0199', '123 Forbes Ave', CURDATE());

-- VERIFY STEP 6: Payment Receipt
SELECT 
    payment_id AS "Receipt #", 
    CONCAT('$', amount) AS "Amount Paid", 
    payment_date AS "Date", 
    payment_method AS "Method"
FROM payment 
ORDER BY payment_id DESC 
LIMIT 1;

-- 7. TOP RENTED MOVIES
SELECT 
    m.title AS "Movie Title", 
    COUNT(r.rental_id) AS "Total Times Rented"
FROM movie m
JOIN inventory_copy ic ON m.movie_id = ic.movie_id
JOIN rental r ON ic.copy_id = r.copy_id
GROUP BY m.title
ORDER BY "Total Times Rented" DESC
LIMIT 5;

-- 8. TOP SPENDING CUSTOMERS
SELECT 
    CONCAT(c.first_name, ' ', c.last_name) AS "Customer Name",
    CONCAT('$', SUM(p.amount)) AS "Total Spent"
FROM customer c
JOIN rental r ON c.customer_id = r.customer_id
JOIN payment p ON r.rental_id = p.rental_id
GROUP BY c.customer_id
ORDER BY SUM(p.amount) DESC;

-- 9. CHECK FOR OVERDUE RENTALS
SELECT 
    CONCAT(c.first_name, ' ', c.last_name) AS "Customer Name", 
    m.title AS "Movie Title", 
    r.due_date AS "Date Due"
FROM rental r
JOIN customer c ON r.customer_id = c.customer_id
JOIN inventory_copy ic ON r.copy_id = ic.copy_id
JOIN movie m ON ic.movie_id = m.movie_id
WHERE r.rental_status = 'OPEN' AND r.due_date < NOW();

-- 10. MASTER RENTAL LOG
SELECT 
    CONCAT(cust.first_name, ' ', cust.last_name) AS "Customer Name",
    r.rental_date AS "Date Rented",
    COALESCE(CONCAT('$', p.amount), 'UNPAID') AS "Payment Status",
    COALESCE(p.payment_method, 'PENDING') AS "Method",
    m.title AS "Movie Title",
    cat.category_name AS "Genre",
    GROUP_CONCAT(DISTINCT a.actor_name ORDER BY a.actor_name SEPARATOR ', ') AS "Starring Actors",
    ic.store_location AS "Shelf Location"
FROM rental r
JOIN customer cust ON r.customer_id = cust.customer_id
LEFT JOIN payment p ON r.rental_id = p.rental_id
JOIN inventory_copy ic ON r.copy_id = ic.copy_id
JOIN movie m ON ic.movie_id = m.movie_id
JOIN movie_category mc ON m.movie_id = mc.movie_id
JOIN category cat ON mc.category_id = cat.category_id
JOIN movie_actor ma ON m.movie_id = ma.movie_id
JOIN actor a ON ma.actor_id = a.actor_id
GROUP BY 
    r.rental_id, 
    cust.first_name, 
    cust.last_name, 
    r.rental_date, 
    p.amount, 
    p.payment_method, 
    m.title, 
    cat.category_name, 
    ic.store_location
ORDER BY r.rental_date DESC;

-- 11. CALCULATE OUTSTANDING DEBT (LATE FEES ONLY)
SELECT 
    CONCAT(c.first_name, ' ', c.last_name) AS "Customer Name",
    m.title AS "Movie Title",
    r.due_date AS "Original Due Date",
    DATEDIFF(NOW(), r.due_date) AS "Days Late",
    CONCAT('$', m.late_fee) AS "Daily Late Fee",
    -- THE CALCULATION
    CONCAT('$', (DATEDIFF(NOW(), r.due_date) * m.late_fee)) AS "Balance Due (Penalty)"
FROM rental r
JOIN inventory_copy ic ON r.copy_id = ic.copy_id
JOIN movie m ON ic.movie_id = m.movie_id
JOIN customer c ON r.customer_id = c.customer_id
WHERE r.rental_status = 'OPEN' AND r.due_date < NOW();