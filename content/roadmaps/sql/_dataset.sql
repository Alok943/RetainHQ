-- =====================================================================
-- RetainHQ — SQL roadmap canonical dataset  (runs in PGlite = real Postgres)
-- ---------------------------------------------------------------------
-- ONE shared e-commerce + HR dataset seeded once per session. EVERY lesson
-- and understanding-check queries THIS schema unless it declares a
-- `query_walkthrough.setup_sql` override (topic-specific extras).
--
-- Design goals (each table earns its place by enabling specific topics):
--   customers  — DISTINCT(country), NULL handling (Emma has NULL country),
--                LEFT JOIN (Greg & Hana have NO orders)
--   products   — categories for GROUP BY / aggregation
--   orders     — statuses for WHERE/CASE, dates for ORDER BY / window frames
--   order_items— the join+aggregation workhorse (SUM, multi-table joins)
--   employees  — self-join (emp->manager), recursive CTE (org chart),
--                window funcs (RANK salary BY department, LEAD/LAG)
--
-- Determinism: small, fixed ids; lessons must add ORDER BY for stable output.
-- Keep this dataset STABLE — lessons hard-code expected result rows against it.
-- =====================================================================

DROP TABLE IF EXISTS order_items, orders, products, customers, employees CASCADE;

CREATE TABLE customers (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  country    TEXT,                       -- NULL on purpose (Emma) for NULL-handling lessons
  signup_date DATE NOT NULL
);
INSERT INTO customers (id, name, country, signup_date) VALUES
  (1, 'Alice',  'US',   DATE '2023-01-15'),
  (2, 'Bob',    'US',   DATE '2023-02-20'),
  (3, 'Carlos', 'MX',   DATE '2023-03-10'),
  (4, 'Diana',  'UK',   DATE '2023-05-05'),
  (5, 'Emma',   NULL,   DATE '2023-06-01'),   -- NULL country
  (6, 'Farah',  'AE',   DATE '2023-07-12'),
  (7, 'Greg',   'US',   DATE '2023-08-30'),   -- no orders (LEFT JOIN)
  (8, 'Hana',   'JP',   DATE '2023-09-14');   -- no orders (LEFT JOIN)

CREATE TABLE products (
  id       INTEGER PRIMARY KEY,
  name     TEXT NOT NULL,
  category TEXT NOT NULL,
  price    NUMERIC(8,2) NOT NULL
);
INSERT INTO products (id, name, category, price) VALUES
  (1, 'Keyboard', 'Electronics', 49.99),
  (2, 'Mouse',    'Electronics', 19.99),
  (3, 'Monitor',  'Electronics', 199.99),
  (4, 'Desk',     'Furniture',   149.99),
  (5, 'Chair',    'Furniture',   89.99),
  (6, 'Notebook', 'Stationery',  4.99);

CREATE TABLE orders (
  id          INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  order_date  DATE NOT NULL,
  status      TEXT NOT NULL                -- 'paid' | 'pending' | 'cancelled'
);
INSERT INTO orders (id, customer_id, order_date, status) VALUES
  (1, 1, DATE '2023-02-01', 'paid'),
  (2, 1, DATE '2023-03-15', 'paid'),
  (3, 2, DATE '2023-04-02', 'pending'),
  (4, 3, DATE '2023-04-20', 'paid'),
  (5, 4, DATE '2023-05-10', 'cancelled'),
  (6, 5, DATE '2023-06-15', 'paid'),
  (7, 6, DATE '2023-07-20', 'paid'),
  (8, 2, DATE '2023-08-01', 'paid');

CREATE TABLE order_items (
  id         INTEGER PRIMARY KEY,
  order_id   INTEGER NOT NULL REFERENCES orders(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity   INTEGER NOT NULL
);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES
  (1,  1, 1, 1),
  (2,  1, 2, 2),
  (3,  2, 3, 1),
  (4,  3, 6, 5),
  (5,  4, 4, 1),
  (6,  4, 5, 2),
  (7,  5, 2, 1),
  (8,  6, 1, 1),
  (9,  6, 6, 3),
  (10, 7, 3, 2),
  (11, 8, 5, 1);

CREATE TABLE employees (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  manager_id INTEGER REFERENCES employees(id),  -- NULL for the CEO (self-join / recursive CTE)
  department TEXT NOT NULL,
  salary     INTEGER NOT NULL
);
INSERT INTO employees (id, name, manager_id, department, salary) VALUES
  (1, 'Sara',   NULL, 'Executive',   200000),  -- CEO, no manager
  (2, 'Tom',    1,    'Engineering', 150000),
  (3, 'Uma',    2,    'Engineering', 120000),
  (4, 'Victor', 2,    'Engineering', 110000),
  (5, 'Wendy',  1,    'Sales',       130000),
  (6, 'Xavier', 5,    'Sales',        95000),
  (7, 'Yara',   5,    'Sales',        90000);
