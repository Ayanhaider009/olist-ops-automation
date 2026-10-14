-- Olist Ops Automation: database schema
-- Run this once in Supabase: SQL Editor > New query > paste > Run

create table if not exists customers (
    customer_id              text primary key,
    customer_unique_id       text,
    customer_zip_code_prefix text,
    customer_city            text,
    customer_state           text
);

create table if not exists sellers (
    seller_id              text primary key,
    seller_zip_code_prefix text,
    seller_city            text,
    seller_state           text
);

create table if not exists products (
    product_id                    text primary key,
    product_category_name         text,
    product_category_name_english text,
    product_weight_g              numeric
);

create table if not exists orders (
    order_id                      text primary key,
    customer_id                   text references customers (customer_id),
    order_status                  text,
    order_purchase_timestamp      timestamp,
    order_approved_at             timestamp,
    order_delivered_carrier_date  timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date timestamp,
    -- filled by the n8n late-delivery workflow
    late_flagged                  boolean default false,
    late_flagged_at               timestamp
);

create table if not exists order_items (
    order_id            text references orders (order_id),
    order_item_id       int,
    product_id          text references products (product_id),
    seller_id           text references sellers (seller_id),
    shipping_limit_date timestamp,
    price               numeric,
    freight_value       numeric,
    primary key (order_id, order_item_id)
);

create table if not exists reviews (
    review_id               text,
    order_id                text references orders (order_id),
    review_score            int,
    review_comment_title    text,
    review_comment_message  text,
    review_creation_date    timestamp,
    review_answer_timestamp timestamp,
    -- filled by the n8n AI review-triage workflow
    ai_translation          text,
    ai_category             text,
    ai_reply_draft          text,
    triaged_at              timestamp,
    primary key (review_id, order_id)
);

-- speeds up the queries the workflows will run
create index if not exists idx_orders_estimated   on orders (order_estimated_delivery_date);
create index if not exists idx_orders_purchase    on orders (order_purchase_timestamp);
create index if not exists idx_reviews_untriaged  on reviews (review_score) where triaged_at is null;
