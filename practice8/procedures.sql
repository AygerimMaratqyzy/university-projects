-- Upsert (insert or update)
CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_phone !~ '^[0-9]+$' THEN
        RAISE EXCEPTION 'Phone must contain only digits!';
    END IF;

    IF EXISTS (SELECT 1 FROM contacts WHERE name = p_name) THEN
        UPDATE contacts
        SET phone = p_phone
        WHERE name = p_name;
    ELSE
        INSERT INTO contacts(name, phone)
        VALUES (p_name, p_phone);
    END IF;
END;
$$;


-- Bulk insert with validation




CREATE OR REPLACE FUNCTION bulk_insert_contacts(
    names TEXT[],
    phones TEXT[]
)
RETURNS TEXT[] AS $$
DECLARE
    i INT;
    invalid_data TEXT[] := ARRAY[]::TEXT[];
BEGIN
    FOR i IN 1..array_length(names, 1) LOOP
        IF phones[i] ~ '^[0-9]{6,15}$' THEN
            IF EXISTS (SELECT 1 FROM contacts WHERE name = names[i]) THEN
                UPDATE contacts 
                SET phone = phones[i] 
                WHERE name = names[i];
            ELSE
                INSERT INTO contacts(name, phone)
                VALUES (names[i], phones[i]);
            END IF;
        ELSE
            invalid_data := array_append(invalid_data, names[i] || ':' || phones[i]);
        END IF;
    END LOOP;

    RETURN invalid_data;
END;
$$ LANGUAGE plpgsql;


-- Delete by name or phone
CREATE OR REPLACE PROCEDURE delete_contact(p_value TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts
    WHERE name = p_value OR phone = p_value;
END;
$$;