CREATE TABLE public.null_price_percent_metrics (
    id SERIAL PRIMARY KEY,
    calculation_date DATE,
    calculation_time TIME,
    percent_null_prices NUMERIC
);

CREATE TABLE public.tqbr_prices (
    id SERIAL PRIMARY KEY,
    quote_date DATE,
    quote_time TIME,
    ticker VARCHAR(255),
    price NUMERIC
);