ALTER TABLE clients_client ADD COLUMN identifier BIGINT;
ALTER TABLE suppliers_supplier ADD COLUMN identifier BIGINT;

SELECT DISTINCT shop_id FROM clients_client;
SELECT DISTINCT shop_id FROM suppliers_supplier;

WITH v_table_name AS
(SELECT id, row_number() OVER () AS ident FROM clients_client WHERE shop_id=2 ORDER BY id)
UPDATE clients_client set identifier = v_table_name.ident
FROM v_table_name
WHERE clients_client.id = v_table_name.id;


ALTER TABLE clients_client ALTER COLUMN identifier SET NOT NULL;
ALTER TABLE suppliers_supplier ALTER COLUMN identifier SET NOT NULL;

ALTER TABLE clients_client ADD CONSTRAINT clients_client_shop_id_identifier_unique UNIQUE (shop_id, identifier);
ALTER TABLE suppliers_supplier ADD CONSTRAINT suppliers_supplier_shop_id_identifier_unique UNIQUE (shop_id, identifier);
