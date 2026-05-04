DROP FUNCTION IF EXISTS get_contacts_paginated(integer, integer);
DROP FUNCTION IF EXISTS search_contacts(text);

CREATE OR REPLACE PROCEDURE upsert_contact(
    p_first_name VARCHAR,
    p_last_name  VARCHAR DEFAULT NULL,
    p_phone      VARCHAR DEFAULT NULL,
    p_phone_type VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INTEGER;
BEGIN
    -- Phone digit-only check (mirrors P8 validation)
    IF p_phone IS NOT NULL AND p_phone !~ '^[0-9]+$' THEN
        RAISE EXCEPTION 'Phone must contain only digits!';
    END IF;

    -- Try to find existing contact by full name
    SELECT id INTO v_id
    FROM contacts
    WHERE first_name = p_first_name
      AND COALESCE(last_name, '') = COALESCE(p_last_name, '');

    IF FOUND THEN
        -- Update: replace phone of the given type if it exists,
        -- otherwise insert a new row into phones
        IF p_phone IS NOT NULL THEN
            IF EXISTS (
                SELECT 1 FROM phones
                WHERE contact_id = v_id AND type = p_phone_type
            ) THEN
                UPDATE phones
                SET phone = p_phone
                WHERE contact_id = v_id AND type = p_phone_type;
            ELSE
                INSERT INTO phones (contact_id, phone, type)
                VALUES (v_id, p_phone, p_phone_type);
            END IF;
        END IF;
    ELSE
        -- Insert new contact
        INSERT INTO contacts (first_name, last_name)
        VALUES (p_first_name, p_last_name)
        RETURNING id INTO v_id;

        IF p_phone IS NOT NULL THEN
            INSERT INTO phones (contact_id, phone, type)
            VALUES (v_id, p_phone, p_phone_type);
        END IF;
    END IF;
END;
$$;


-- Bulk insert,adapted from p8
CREATE OR REPLACE FUNCTION bulk_insert_contacts(
    first_names TEXT[],
    last_names  TEXT[],
    phones      TEXT[]
)
RETURNS TEXT[] AS $$
DECLARE
    i            INT;
    v_id         INTEGER;
    invalid_data TEXT[] := ARRAY[]::TEXT[];
BEGIN
    FOR i IN 1..array_length(first_names, 1) LOOP
        IF phones[i] ~ '^[0-9]{6,15}$' THEN
            SELECT id INTO v_id
            FROM contacts
            WHERE first_name = first_names[i]
              AND COALESCE(last_name, '') = COALESCE(last_names[i], '');

            IF FOUND THEN
                -- update first mobile phone
                UPDATE phones
                SET phone = phones[i]
                WHERE contact_id = v_id AND type = 'mobile';
            ELSE
                INSERT INTO contacts (first_name, last_name)
                VALUES (first_names[i], last_names[i])
                RETURNING id INTO v_id;

                INSERT INTO phones (contact_id, phone, type)
                VALUES (v_id, phones[i], 'mobile');
            END IF;
        ELSE
            invalid_data := array_append(
                invalid_data,
                first_names[i] || ' ' || COALESCE(last_names[i], '') || ':' || phones[i]
            );
        END IF;
    END LOOP;

    RETURN invalid_data;
END;
$$ LANGUAGE plpgsql;


-- Delete by name or phone (P8 logic, adapted for new schema)
CREATE OR REPLACE PROCEDURE delete_contact(p_value TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts
    WHERE first_name = p_value
       OR (first_name || ' ' || COALESCE(last_name, '')) = p_value
       OR id IN (
           SELECT contact_id FROM phones WHERE phone = p_value
       );
END;
$$;


-- Paginated listing (P8 get_contacts_paginated, updated columns)
CREATE OR REPLACE FUNCTION get_contacts_paginated(p_limit INT, p_offset INT)
RETURNS TABLE(
    id         INT,
    full_name  TEXT,
    email      VARCHAR,
    birthday   DATE,
    grp        VARCHAR,
    phones_csv TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        (c.first_name || ' ' || COALESCE(c.last_name, ''))::TEXT   AS full_name,
        c.email,
        c.birthday,
        g.name                                                        AS grp,
        STRING_AGG(p.phone || ' (' || p.type || ')', ', '
                   ORDER BY p.type)                                   AS phones_csv
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    GROUP BY c.id, c.first_name, c.last_name, c.email,
             c.birthday, g.name, c.created_at
    ORDER BY c.first_name, c.last_name
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,   -- "First" or "First Last"
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INTEGER;
BEGIN
    -- Accept both "First" and "First Last"
    SELECT id INTO v_id
    FROM contacts
    WHERE first_name = split_part(p_contact_name, ' ', 1)
      AND (
          p_contact_name NOT LIKE '% %'                          -- only first name given
          OR COALESCE(last_name, '') =
             TRIM(SUBSTRING(p_contact_name FROM POSITION(' ' IN p_contact_name) + 1))
      )
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    IF p_phone !~ '^[0-9]+$' THEN
        RAISE EXCEPTION 'Phone must contain only digits!';
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Phone type must be home, work, or mobile.';
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_id, p_phone, p_type);
END;
$$;


--move_to_group
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Resolve contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name = split_part(p_contact_name, ' ', 1)
      AND (
          p_contact_name NOT LIKE '% %'
          OR COALESCE(last_name, '') =
             TRIM(SUBSTRING(p_contact_name FROM POSITION(' ' IN p_contact_name) + 1))
      )
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Resolve or create group
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    IF NOT FOUND THEN
        INSERT INTO groups (name) VALUES (p_group_name)
        RETURNING id INTO v_group_id;
        RAISE NOTICE 'Created new group "%".', p_group_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
END;
$$;


-- search contacts
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id         INT,
    full_name  TEXT,
    email      VARCHAR,
    birthday   DATE,
    grp        VARCHAR,
    phones_csv TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (c.id)
        c.id,
        (c.first_name || ' ' || COALESCE(c.last_name, ''))::TEXT AS full_name,
        c.email,
        c.birthday,
        g.name                                                     AS grp,
        (
            SELECT STRING_AGG(p2.phone || ' (' || p2.type || ')', ', '
                              ORDER BY p2.type)
            FROM phones p2
            WHERE p2.contact_id = c.id
        )                                                          AS phones_csv
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE
        c.first_name ILIKE '%' || p_query || '%'
     OR COALESCE(c.last_name, '') ILIKE '%' || p_query || '%'
     OR COALESCE(c.email,     '') ILIKE '%' || p_query || '%'
     OR p.phone ILIKE '%' || p_query || '%'
    ORDER BY c.id, c.first_name;
END;
$$ LANGUAGE plpgsql;


--helper view
CREATE OR REPLACE VIEW v_contacts AS
SELECT
    c.id,
    c.first_name,
    COALESCE(c.last_name, '')                                     AS last_name,
    (c.first_name || ' ' || COALESCE(c.last_name, ''))           AS full_name,
    c.email,
    c.birthday,
    c.created_at,
    g.name                                                        AS grp,
    STRING_AGG(p.phone || ' (' || p.type || ')', ', '
               ORDER BY p.type)                                   AS phones_csv
FROM contacts c
LEFT JOIN groups g ON g.id = c.group_id
LEFT JOIN phones p ON p.contact_id = c.id
GROUP BY c.id, c.first_name, c.last_name,
         c.email, c.birthday, c.created_at, g.name;
