USE decisioniq;

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100),
    age INT,
    gender VARCHAR(20),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    signup_date DATE,
    acquisition_channel VARCHAR(50)
);

CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(150),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    cost_price DECIMAL(10,2),
    selling_price DECIMAL(10,2),
    supplier VARCHAR(100)
);

CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20),
    order_date DATE,
    order_status VARCHAR(30),
    payment_method VARCHAR(50),
    shipping_cost DECIMAL(10,2),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20),
    product_id VARCHAR(20),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount_pct DECIMAL(5,2),

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

CREATE TABLE returns (
    return_id VARCHAR(20) PRIMARY KEY,
    order_item_id VARCHAR(20),
    return_date DATE,
    return_reason VARCHAR(100),
    refund_amount DECIMAL(10,2),

    FOREIGN KEY (order_item_id)
        REFERENCES order_items(order_item_id)
);

CREATE TABLE website_sessions (
    session_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20),
    session_date DATE,
    device VARCHAR(30),
    traffic_source VARCHAR(50),
    pages_viewed INT,
    session_duration_seconds INT,
    added_to_cart BOOLEAN,
    converted BOOLEAN,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE marketing_campaigns (
    campaign_id VARCHAR(20) PRIMARY KEY,
    campaign_name VARCHAR(100),
    channel VARCHAR(50),
    campaign_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    campaign_budget DECIMAL(12,2)
);

CREATE TABLE campaign_performance (
    performance_id VARCHAR(20) PRIMARY KEY,
    campaign_id VARCHAR(20),
    date DATE,
    impressions INT,
    clicks INT,
    ad_spend DECIMAL(12,2),
    conversions INT,
    revenue_generated DECIMAL(12,2),

    FOREIGN KEY (campaign_id)
        REFERENCES marketing_campaigns(campaign_id)
);



SHOW TABLES;