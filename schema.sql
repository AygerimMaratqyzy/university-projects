--1 Drop in safe order (child tables first)
DROP TABLE IF EXISTS phones   CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS groups   CASCADE;

--2. Groups / categories
CREATE TABLE groups (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(50)  UNIQUE NOT NULL
);

-- Seed the four standard categories
INSERT INTO groups (name) VALUES
    ('Family'),
    ('Work'),
    ('Friend'),
    ('Other');

-- 3. Contacts (extended from P7/P8)
CREATE TABLE contacts (
    id         SERIAL        PRIMARY KEY,
    first_name VARCHAR(50)   NOT NULL,
    last_name  VARCHAR(50),
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER       REFERENCES groups(id) ON DELETE SET NULL,
    created_at TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- Composite unique index – same logic as P8's upsert_contact
CREATE UNIQUE INDEX contacts_fullname_unique
    ON contacts (first_name, COALESCE(last_name, ''));

--4. Phones (1-to-many)
CREATE TABLE phones (
    id         SERIAL      PRIMARY KEY,
    contact_id INTEGER     NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) NOT NULL DEFAULT 'mobile'
                           CHECK (type IN ('home', 'work', 'mobile'))
);