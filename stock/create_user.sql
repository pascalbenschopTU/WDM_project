CREATE ROLE postgres superuser;
CREATE USER postgres;
GRANT ROOT TO postgres;
GRANT ALL privileges ON DATABASE stock to postgres;