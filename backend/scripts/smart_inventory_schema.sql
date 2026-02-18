--=============================================================================
-- Smart Inventory System – Complete MySQL Schema
-- Version 3.0 – Dynamic, Extensible, No Sample Data
-- =============================================================================

DROP DATABASE IF EXISTS smart_inventory_db;
CREATE DATABASE smart_inventory_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_inventory_db;

-- -----------------------------------------------------------------------------
-- 1. LOOKUP TABLES (Fully dynamic – no ENUMs, no hardcoded strings)
-- -----------------------------------------------------------------------------

-- 1.1 User roles – any role can be defined (admin, manager, clerk, etc.)
CREATE TABLE roles (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.2 Product categories – free classification
CREATE TABLE categories (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.3 Movement types – defines all possible stock operations
CREATE TABLE movement_types (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,      -- e.g., 'sale', 'receipt', 'adjustment', 'return', 'damage'
    description TEXT,
    sign TINYINT NOT NULL DEFAULT 1,        -- +1 = increases stock, -1 = decreases stock
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 2. CORE ENTITY TABLES
-- -----------------------------------------------------------------------------

-- 2.1 Suppliers
CREATE TABLE suppliers (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(120),
    address TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.2 Users
CREATE TABLE users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3 User–Roles (many‑to‑many)
CREATE TABLE user_roles (
    user_id INT UNSIGNED NOT NULL,
    role_id INT UNSIGNED NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.4 Products (SKU is user‑defined business key)
CREATE TABLE products (
    sku VARCHAR(50) NOT NULL,
    barcode VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    category_id INT UNSIGNED,
    supplier_id INT UNSIGNED,
    cost_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    quantity_in_stock INT NOT NULL DEFAULT 0,
    reorder_threshold INT NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (sku),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    INDEX idx_barcode (barcode),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 3. TRANSACTION & MOVEMENT TABLES
-- -----------------------------------------------------------------------------

-- 3.1 Sale Transactions (header)
CREATE TABLE sale_transactions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    transaction_number VARCHAR(50) NOT NULL UNIQUE,
    user_id INT UNSIGNED NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_transaction_number (transaction_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3.2 Sale Line Items (detail)
CREATE TABLE sale_line_items (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    transaction_id INT UNSIGNED NOT NULL,
    product_sku VARCHAR(50) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (transaction_id) REFERENCES sale_transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (product_sku) REFERENCES products(sku) ON DELETE RESTRICT,
    INDEX idx_transaction (transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3.3 Stock Movements (complete audit trail)
CREATE TABLE stock_movements (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_sku VARCHAR(50) NOT NULL,
    movement_type_id INT UNSIGNED NOT NULL,
    quantity INT NOT NULL,                    -- absolute quantity (positive)
    previous_quantity INT NOT NULL,           -- snapshot before change
    new_quantity INT NOT NULL,               -- snapshot after change
    reference_id VARCHAR(100),              -- e.g., sale_transaction.id, purchase_order.id
    reason VARCHAR(255),                   -- mandatory for adjustments/damage
    created_by INT UNSIGNED NOT NULL,       -- user who performed the action
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (product_sku) REFERENCES products(sku) ON DELETE RESTRICT,
    FOREIGN KEY (movement_type_id) REFERENCES movement_types(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_product (product_sku),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3.4 Replenishment Suggestions (output of predictive engine)
CREATE TABLE replenishment_suggestions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_sku VARCHAR(50) NOT NULL,
    date_generated DATE NOT NULL,
    forecasted_demand INT NOT NULL,
    current_stock INT NOT NULL,
    suggested_quantity INT NOT NULL,
    is_acted_upon BOOLEAN NOT NULL DEFAULT FALSE,
    acted_upon_at TIMESTAMP NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (product_sku) REFERENCES products(sku) ON DELETE CASCADE,
    INDEX idx_date (date_generated),
    INDEX idx_acted (is_acted_upon)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3.5 Audit Log (optional – for full traceability)
CREATE TABLE audit_log (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    table_name VARCHAR(50) NOT NULL,
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    old_data JSON,
    new_data JSON,
    changed_by INT UNSIGNED,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 4. TRIGGERS
-- -----------------------------------------------------------------------------

-- 4.1 Before inserting a sale line item: check stock, calculate line total
DELIMITER $$
CREATE TRIGGER before_sale_line_item_insert
BEFORE INSERT ON sale_line_items
FOR EACH ROW
BEGIN
    DECLARE current_stock INT;
    DECLARE movement_id INT;

    -- Get current stock
    SELECT quantity_in_stock INTO current_stock
    FROM products
    WHERE sku = NEW.product_sku
    FOR UPDATE;

    -- Prevent negative stock
    IF current_stock < NEW.quantity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient stock for this product';
    END IF;

    -- Calculate line total
    SET NEW.line_total = NEW.quantity * NEW.unit_price;
END$$
DELIMITER ;

-- 4.2 After inserting a sale line item: update stock, log movement, update transaction total
DELIMITER $$
CREATE TRIGGER after_sale_line_item_insert
AFTER INSERT ON sale_line_items
FOR EACH ROW
BEGIN
    DECLARE current_qty INT;
    DECLARE new_qty INT;
    DECLARE sale_user_id INT;
    DECLARE sale_movement_type_id INT;

    -- Get the user who processed the sale
    SELECT user_id INTO sale_user_id
    FROM sale_transactions
    WHERE id = NEW.transaction_id;

    -- Get movement_type_id for 'sale' (dynamic lookup)
    SELECT id INTO sale_movement_type_id
    FROM movement_types
    WHERE name = 'sale'
    LIMIT 1;

    -- Get current quantity (with lock)
    SELECT quantity_in_stock INTO current_qty
    FROM products
    WHERE sku = NEW.product_sku
    FOR UPDATE;

    SET new_qty = current_qty - NEW.quantity;

    -- Update product stock
    UPDATE products
    SET quantity_in_stock = new_qty
    WHERE sku = NEW.product_sku;

    -- Log stock movement
    INSERT INTO stock_movements (
        product_sku,
        movement_type_id,
        quantity,
        previous_quantity,
        new_quantity,
        reference_id,
        created_by
    ) VALUES (
        NEW.product_sku,
        sale_movement_type_id,
        NEW.quantity,
        current_qty,
        new_qty,
        NEW.transaction_id,
        sale_user_id
    );

    -- Update sale transaction total
    UPDATE sale_transactions
    SET total_amount = total_amount + NEW.line_total
    WHERE id = NEW.transaction_id;
END$$
DELIMITER ;

-- 4.3 After inserting a stock movement of type 'receipt' or 'return': increase stock
DELIMITER $$
CREATE TRIGGER after_stock_movement_receipt
AFTER INSERT ON stock_movements
FOR EACH ROW
BEGIN
    DECLARE receipt_movement_type_id INT;
    DECLARE return_movement_type_id INT;

    -- Get movement type IDs
    SELECT id INTO receipt_movement_type_id FROM movement_types WHERE name = 'receipt' LIMIT 1;
    SELECT id INTO return_movement_type_id FROM movement_types WHERE name = 'return' LIMIT 1;

    IF NEW.movement_type_id IN (receipt_movement_type_id, return_movement_type_id) THEN
        UPDATE products
        SET quantity_in_stock = quantity_in_stock + NEW.quantity
        WHERE sku = NEW.product_sku;
    END IF;
END$$
DELIMITER ;

-- 4.4 Before stock movement: validate and set previous/new quantities
DELIMITER $$
CREATE TRIGGER before_stock_movement_insert
BEFORE INSERT ON stock_movements
FOR EACH ROW
BEGIN
    DECLARE current_qty INT;
    DECLARE movement_sign INT;

    -- Get current stock
    SELECT quantity_in_stock INTO current_qty
    FROM products
    WHERE sku = NEW.product_sku
    FOR UPDATE;

    -- Get sign of this movement type
    SELECT sign INTO movement_sign
    FROM movement_types
    WHERE id = NEW.movement_type_id;

    -- Set snapshots
    SET NEW.previous_quantity = current_qty;
    SET NEW.new_quantity = current_qty + (NEW.quantity * movement_sign);
END$$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- 5. STORED PROCEDURES
-- -----------------------------------------------------------------------------

-- 5.1 Process a complete sale with multiple items (atomic operation)
DELIMITER $$
CREATE PROCEDURE ProcessSale(
    IN p_transaction_number VARCHAR(50),
    IN p_user_id INT UNSIGNED,
    IN p_transaction_date DATE,
    IN p_items JSON  -- Format: [{"sku":"...", "quantity":2, "unit_price":15.00}, ...]
)
BEGIN
    DECLARE v_transaction_id INT UNSIGNED;
    DECLARE v_i INT DEFAULT 0;
    DECLARE v_len INT;
    DECLARE v_sku VARCHAR(50);
    DECLARE v_qty INT;
    DECLARE v_price DECIMAL(10,2);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Create sale header (total_amount will be updated by triggers)
    INSERT INTO sale_transactions (transaction_number, user_id, transaction_date, total_amount)
    VALUES (p_transaction_number, p_user_id, p_transaction_date, 0);

    SET v_transaction_id = LAST_INSERT_ID();
    SET v_len = JSON_LENGTH(p_items);

    WHILE v_i < v_len DO
        SET v_sku = JSON_UNQUOTE(JSON_EXTRACT(p_items, CONCAT('$[', v_i, '].sku')));
        SET v_qty = JSON_EXTRACT(p_items, CONCAT('$[', v_i, '].quantity'));
        SET v_price = JSON_EXTRACT(p_items, CONCAT('$[', v_i, '].unit_price'));

        INSERT INTO sale_line_items (transaction_id, product_sku, quantity, unit_price, line_total)
        VALUES (v_transaction_id, v_sku, v_qty, v_price, 0);  -- line_total will be set by trigger

        SET v_i = v_i + 1;
    END WHILE;

    COMMIT;

    SELECT v_transaction_id AS transaction_id;
END$$
DELIMITER ;

-- 5.2 Generate replenishment suggestions using moving average
DELIMITER $$
CREATE PROCEDURE GenerateReplenishmentSuggestions(
    IN p_lookback_days INT,        -- e.g., 30
    IN p_forecast_days INT,        -- e.g., 7
    IN p_safety_stock_factor DECIMAL(3,2)  -- e.g., 1.5
)
BEGIN
    DECLARE v_sale_movement_type_id INT;

    -- Get movement type ID for 'sale'
    SELECT id INTO v_sale_movement_type_id FROM movement_types WHERE name = 'sale' LIMIT 1;

    -- Insert new suggestions (overwrites previous ones for today)
    REPLACE INTO replenishment_suggestions (
        product_sku,
        date_generated,
        forecasted_demand,
        current_stock,
        suggested_quantity,
        is_acted_upon
    )
    SELECT
        p.sku,
        CURDATE(),
        COALESCE(ROUND(AVG(sm.quantity) * (p_forecast_days / 1)), 0) AS forecast,
        p.quantity_in_stock,
        GREATEST(
            0,
            ROUND(
                (COALESCE(AVG(sm.quantity), 0) * (p_forecast_days / 1) * p_safety_stock_factor)
                - p.quantity_in_stock
            )
        ) AS suggested_qty,
        FALSE
    FROM products p
    LEFT JOIN stock_movements sm ON p.sku = sm.product_sku
        AND sm.movement_type_id = v_sale_movement_type_id
        AND sm.created_at >= CURDATE() - INTERVAL p_lookback_days DAY
    WHERE p.is_active = TRUE
    GROUP BY p.sku, p.quantity_in_stock;
END$$
DELIMITER ;

-- 5.3 Add a new stock receipt (increases stock, logs movement)
DELIMITER $$
CREATE PROCEDURE AddStockReceipt(
    IN p_sku VARCHAR(50),
    IN p_quantity INT,
    IN p_reference VARCHAR(100),
    IN p_user_id INT UNSIGNED
)
BEGIN
    DECLARE v_receipt_movement_type_id INT;

    SELECT id INTO v_receipt_movement_type_id
    FROM movement_types
    WHERE name = 'receipt'
    LIMIT 1;

    INSERT INTO stock_movements (
        product_sku,
        movement_type_id,
        quantity,
        reference_id,
        created_by
    ) VALUES (
        p_sku,
        v_receipt_movement_type_id,
        p_quantity,
        p_reference,
        p_user_id
    );
END$$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- 6. VIEWS (for reporting and dashboards)
-- -----------------------------------------------------------------------------

-- 6.1 Low stock alerts
CREATE VIEW low_stock_alerts AS
SELECT
    p.sku,
    p.name,
    p.quantity_in_stock,
    p.reorder_threshold,
    CONCAT('Stock below reorder level (', p.quantity_in_stock, ' < ', p.reorder_threshold, ')') AS alert_message
FROM products p
WHERE p.quantity_in_stock <= p.reorder_threshold
  AND p.is_active = TRUE;

-- 6.2 Daily sales summary
CREATE VIEW daily_sales_summary AS
SELECT
    st.transaction_date,
    COUNT(DISTINCT st.id) AS transaction_count,
    COUNT(DISTINCT sli.product_sku) AS unique_products_sold,
    SUM(sli.quantity) AS total_items_sold,
    SUM(st.total_amount) AS total_revenue
FROM sale_transactions st
JOIN sale_line_items sli ON st.id = sli.transaction_id
GROUP BY st.transaction_date
ORDER BY st.transaction_date DESC;

-- 6.3 Product performance (last 30 days turnover)
CREATE VIEW product_performance AS
SELECT
    p.sku,
    p.name,
    c.name AS category_name,
    p.quantity_in_stock,
    COALESCE(SUM(sm.quantity), 0) AS total_sold_30d,
    COALESCE(ROUND(SUM(sm.quantity) / 30, 2), 0) AS avg_daily_sales,
    CASE
        WHEN COALESCE(SUM(sm.quantity), 0) = 0 THEN 'No sales'
        WHEN p.quantity_in_stock = 0 THEN 'Out of stock'
        WHEN p.quantity_in_stock <= p.reorder_threshold THEN 'Reorder needed'
        ELSE 'OK'
    END AS status
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN stock_movements sm ON p.sku = sm.product_sku
    AND sm.movement_type_id = (SELECT id FROM movement_types WHERE name = 'sale' LIMIT 1)
    AND sm.created_at >= CURDATE() - INTERVAL 30 DAY
WHERE p.is_active = TRUE
GROUP BY p.sku, p.name, c.name, p.quantity_in_stock, p.reorder_threshold;

-- 6.4 Stock movement history (human readable)
CREATE VIEW stock_movement_log AS
SELECT
    sm.id,
    p.name AS product_name,
    p.sku,
    mt.name AS movement_type,
    sm.quantity,
    sm.previous_quantity,
    sm.new_quantity,
    sm.reference_id,
    sm.reason,
    u.username AS performed_by,
    sm.created_at
FROM stock_movements sm
JOIN products p ON sm.product_sku = p.sku
JOIN movement_types mt ON sm.movement_type_id = mt.id
LEFT JOIN users u ON sm.created_by = u.id
ORDER BY sm.created_at DESC;

-- 6.5 Current inventory snapshot
CREATE VIEW current_inventory AS
SELECT
    p.sku,
    p.name,
    c.name AS category,
    p.quantity_in_stock,
    p.reorder_threshold,
    p.selling_price,
    (p.quantity_in_stock * p.selling_price) AS potential_revenue,
    p.is_active
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.is_active = TRUE;

-- -----------------------------------------------------------------------------
-- 7. INDEXES FOR PERFORMANCE (additional indexes beyond those already defined)
-- -----------------------------------------------------------------------------
CREATE INDEX idx_stock_movements_composite ON stock_movements(product_sku, created_at);
CREATE INDEX idx_sale_line_items_product ON sale_line_items(product_sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);

-- =============================================================================
-- END OF SCHEMA – NO SAMPLE DATA INSERTED
-- =============================================================================