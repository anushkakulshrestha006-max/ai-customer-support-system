-- AI Customer Support Database Schema
-- Simple, clean relational schema for students and interview demonstrations

CREATE DATABASE IF NOT EXISTS ai_customer_support;
USE ai_customer_support;

-- 1. Customers Table: Stores basic customer profiles
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Conversations Table: Stores Q&A history between customer and AI
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversations_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(id) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Tickets Table: Stores support tickets raised when issues are unresolved
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    issue TEXT NOT NULL,
    category ENUM('Payment', 'Delivery', 'Refund', 'Cancellation', 'Account', 'Other') DEFAULT 'Other',
    status ENUM('Open', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tickets_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(id) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
