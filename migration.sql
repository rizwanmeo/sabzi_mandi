ALTER TABLE clients_client ADD COLUMN identifier BIGINT;
ALTER TABLE suppliers_supplier ADD COLUMN identifier BIGINT;

SELECT DISTINCT shop_id FROM clients_client;
SELECT DISTINCT shop_id FROM suppliers_supplier;

WITH v_table_name AS
(SELECT id, row_number() OVER () AS ident FROM clients_client WHERE shop_id=1 ORDER BY id)
UPDATE clients_client set identifier = v_table_name.ident
FROM v_table_name
WHERE clients_client.id = v_table_name.id;

WITH v_table_name AS
(SELECT id, row_number() OVER () AS ident FROM suppliers_supplier WHERE shop_id=1 ORDER BY id)
UPDATE suppliers_supplier set identifier = v_table_name.ident
FROM v_table_name
WHERE suppliers_supplier.id = v_table_name.id;


ALTER TABLE clients_client ALTER COLUMN identifier SET NOT NULL;
ALTER TABLE suppliers_supplier ALTER COLUMN identifier SET NOT NULL;

ALTER TABLE clients_client ADD CONSTRAINT clients_client_shop_id_identifier_unique UNIQUE (shop_id, identifier);
ALTER TABLE suppliers_supplier ADD CONSTRAINT suppliers_supplier_shop_id_identifier_unique UNIQUE (shop_id, identifier);

SELECT l.id, l.tx_id, l.tx_time, l.tx_date, l.balance, l.bill_amount, l.payment_amount, l.description, l.client_id
FROM ledger_clientledger l
JOIN (
    SELECT max(ledger_clientledger.id) AS id, ledger_clientledger.client_id
    FROM ledger_clientledger
    GROUP BY ledger_clientledger.client_id
    ) r USING (id);


CREATE OR REPLACE VIEW supplier_ledger_editable AS
SELECT l.id, l.tx_id, l.tx_time, l.tx_date, l.balance, l.bill_amount, l.payment_amount, l.description, l.supplier_id
FROM supplier_ledger l
JOIN (
    SELECT max(supplier_ledger.id) AS id, supplier_ledger.supplier_id
    FROM supplier_ledger
    GROUP BY supplier_ledger.supplier_id
    ) r USING (id);



ALTER TABLE ledger_clientledger ADD CONSTRAINT client_ledger_tx_id_unique UNIQUE (tx_id);
ALTER TABLE supplier_ledger ADD CONSTRAINT supplier_ledger_tx_id_unique UNIQUE (tx_id);

SELECT l.id, l.tx_id, l.tx_time, l.tx_date, l.balance, l.bill_amount, l.supplier_id FROM supplier_ledger l where tx_id like 'bill%';
