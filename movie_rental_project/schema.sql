-- Reset the database (safe to run multiple times during development)
DROP DATABASE IF EXISTS movierental;
CREATE DATABASE movierental;
USE movierental;

-- 1. CUSTOMER
CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    phone       VARCHAR(20),
    address     VARCHAR(255),
    signup_date DATE NOT NULL
) ENGINE=InnoDB;

-- 2. MOVIE
CREATE TABLE movie (
    movie_id       INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(200) NOT NULL,
    release_year   INT,
    mpaa_rating    VARCHAR(10),
    length_minutes INT,
    movie_rating   DECIMAL(3,1),
    description    TEXT
) ENGINE=InnoDB;

-- 3. CATEGORY
CREATE TABLE category (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 4. MOVIE_CATEGORY
CREATE TABLE movie_category (
    movie_id    INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (movie_id, category_id),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category(category_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 5. ACTOR
CREATE TABLE actor (
    actor_id   INT AUTO_INCREMENT PRIMARY KEY,
    actor_name VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- 6. MOVIE_ACTOR
CREATE TABLE movie_actor (
    movie_id  INT NOT NULL,
    actor_id  INT NOT NULL,
    role_name VARCHAR(100),
    PRIMARY KEY (movie_id, actor_id),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES actor(actor_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 7. INVENTORY_COPY
CREATE TABLE inventory_copy (
    copy_id        INT AUTO_INCREMENT PRIMARY KEY,
    movie_id       INT NOT NULL,
    status         ENUM('AVAILABLE', 'RENTED', 'LOST') NOT NULL DEFAULT 'AVAILABLE',
    store_location VARCHAR(100),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. RENTAL
CREATE TABLE rental (
    rental_id     INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT NOT NULL,
    copy_id       INT NOT NULL,
    rental_date   DATETIME NOT NULL,
    due_date      DATETIME NOT NULL,
    return_date   DATETIME,
    rental_status ENUM('OPEN', 'RETURNED', 'LATE') NOT NULL DEFAULT 'OPEN',
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (copy_id) REFERENCES inventory_copy(copy_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 9. PAYMENT
CREATE TABLE payment (
    payment_id     INT AUTO_INCREMENT PRIMARY KEY,
    rental_id      INT NOT NULL,
    amount         DECIMAL(8,2) NOT NULL,
    payment_date   DATETIME NOT NULL,
    payment_method ENUM('CASH', 'CARD') NOT NULL,
    FOREIGN KEY (rental_id) REFERENCES rental(rental_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Sample data

-- Customers
INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES
('Alice', 'Johnson', 'alice@example.com', '412-111-2222', '123 Main St', '2024-01-01'),
('Bob',   'Lee',     'bob@example.com',   '412-333-4444', '456 Oak Ave', '2024-02-10');

-- Movies
INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description) VALUES
('The Matrix', 1999, 'R',     136, 8.7, 'A hacker discovers reality is a simulation.'),
('Inception',  2010, 'PG-13', 148, 8.8, 'A thief enters dreams to steal secrets.'),
('Toy Story',  1995, 'G',      81, 8.3, 'Animated toys come to life.');

-- Categories
INSERT INTO category (category_name) VALUES
('Action'),
('Sci-Fi'),
('Animation'),
('Family');

-- Movie-Category
INSERT INTO movie_category (movie_id, category_id) VALUES
(1, 1),
(1, 2),
(2, 1),
(2, 2),
(3, 3),
(3, 4);

-- Actors
INSERT INTO actor (actor_name) VALUES
('Keanu Reeves'),
('Laurence Fishburne'),
('Leonardo DiCaprio'),
('Tom Hanks');

-- Movie-Actor
INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES
(1, 1, 'Neo'),
(1, 2, 'Morpheus'),
(2, 3, 'Cobb'),
(3, 4, 'Woody (voice)');

-- Inventory copies
INSERT INTO inventory_copy (movie_id, status, store_location) VALUES
(1, 'AVAILABLE', 'Front Shelf'),
(1, 'AVAILABLE', 'Back Shelf'),
(2, 'AVAILABLE', 'Front Shelf'),
(3, 'AVAILABLE', 'Kids Section');

-- Example rentals
INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status)
VALUES
(1, 1, '2025-11-01 10:00:00', '2025-11-05 10:00:00', 'OPEN'),
(2, 3, '2025-10-20 14:00:00', '2025-10-25 14:00:00', 'RETURNED');

UPDATE inventory_copy SET status = 'RENTED' WHERE copy_id = 1;