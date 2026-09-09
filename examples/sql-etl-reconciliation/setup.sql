DROP TABLE IF EXISTS source_transactions;
DROP TABLE IF EXISTS target_transactions_good;
DROP TABLE IF EXISTS target_transactions_regression;

CREATE TABLE source_transactions (
  transaction_id TEXT PRIMARY KEY,
  amount TEXT NOT NULL,
  status TEXT NOT NULL,
  event_time TEXT NOT NULL
);

CREATE TABLE target_transactions_good (
  transaction_id TEXT PRIMARY KEY,
  amount TEXT NOT NULL,
  status TEXT NOT NULL,
  event_time TEXT NOT NULL
);

CREATE TABLE target_transactions_regression (
  transaction_id TEXT PRIMARY KEY,
  amount TEXT NOT NULL,
  status TEXT NOT NULL,
  event_time TEXT NOT NULL
);

INSERT INTO source_transactions VALUES
  ('TX-001', '0.00',   'POSTED', '2026-09-09T10:00:00Z'),
  ('TX-002', '125.50', 'POSTED', '2026-09-09T10:01:00Z'),
  ('TX-003', '42.10',  'PENDING','2026-09-09T10:02:00Z');

INSERT INTO target_transactions_good
SELECT * FROM source_transactions;

INSERT INTO target_transactions_regression VALUES
  ('TX-001', '0',      'POSTED', '2026-09-09T10:00:00Z'),
  ('TX-002', '125.5',  'POSTED', '2026-09-09T10:01:00Z');
