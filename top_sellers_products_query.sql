WITH purchase_events AS (
    SELECT
        e.user_id,
        e.ga_session_id,
        e.country,
        e.device,
        e.item_id,
        date(e.date) AS purchase_date,
        substr(e.date, 1, 7) AS purchase_month,
        i.name AS product_name,
        i.variant,
        i.category,
        CAST(i.price_in_usd AS REAL) AS price_in_usd,
        CAST(u.ltv AS REAL) AS customer_ltv,
        date(u.date) AS customer_start_date
    FROM events e
    INNER JOIN items i
        ON CAST(e.item_id AS INTEGER) = CAST(i.id AS INTEGER)
    LEFT JOIN users u
        ON CAST(e.user_id AS INTEGER) = CAST(u.id AS INTEGER)
    WHERE e.type = 'purchase'
),
product_country_units AS (
    SELECT
        item_id,
        country,
        COUNT(*) AS country_units,
        ROW_NUMBER() OVER (
            PARTITION BY item_id
            ORDER BY COUNT(*) DESC, country
        ) AS country_rank
    FROM purchase_events
    GROUP BY item_id, country
),
product_rollup AS (
    SELECT
        pe.item_id,
        pe.product_name,
        pe.variant,
        pe.category,
        COUNT(*) AS units_sold,
        ROUND(SUM(pe.price_in_usd), 2) AS revenue_usd,
        COUNT(DISTINCT pe.user_id) AS unique_buyers,
        COUNT(DISTINCT pe.ga_session_id) AS purchase_sessions,
        ROUND(AVG(pe.price_in_usd), 2) AS avg_unit_price_usd,
        ROUND(AVG(pe.customer_ltv), 2) AS avg_buyer_ltv_usd,
        MIN(pe.purchase_date) AS first_purchase_date,
        MAX(pe.purchase_date) AS last_purchase_date
    FROM purchase_events pe
    GROUP BY
        pe.item_id,
        pe.product_name,
        pe.variant,
        pe.category
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY pr.units_sold DESC, pr.revenue_usd DESC, pr.product_name
    ) AS product_rank,
    pr.item_id,
    pr.product_name,
    pr.variant,
    pr.category,
    pr.units_sold,
    pr.revenue_usd,
    pr.unique_buyers,
    pr.purchase_sessions,
    pr.avg_unit_price_usd,
    pr.avg_buyer_ltv_usd,
    pcu.country AS top_country,
    pcu.country_units AS top_country_units,
    pr.first_purchase_date,
    pr.last_purchase_date
FROM product_rollup pr
LEFT JOIN product_country_units pcu
    ON pr.item_id = pcu.item_id
   AND pcu.country_rank = 1
ORDER BY
    pr.units_sold DESC,
    pr.revenue_usd DESC,
    pr.product_name
LIMIT 25;
