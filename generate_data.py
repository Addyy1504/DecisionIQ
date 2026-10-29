import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from pathlib import Path


# -----------------------------
# CONFIGURATION
# -----------------------------

NUM_CUSTOMERS = 15000
NUM_PRODUCTS = 500
NUM_ORDERS = 60000

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)

RANDOM_SEED = 42


# -----------------------------
# RANDOM SEED
# -----------------------------

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


# -----------------------------
# OUTPUT DIRECTORY
# -----------------------------

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)





# -----------------------------
# CUSTOMER DATA
# -----------------------------

first_names = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Kabir",
    "Ananya", "Diya", "Ishita", "Meera", "Riya",
    "Rahul", "Rohan", "Karan", "Sneha", "Nisha",
    "Aman", "Neha", "Priya", "Varun", "Simran"
]

last_names = [
    "Sharma", "Verma", "Gupta", "Mehta", "Kapoor",
    "Malhotra", "Singh", "Patel", "Jain", "Bansal"
]

cities = [
    "Delhi", "Mumbai", "Bengaluru", "Hyderabad",
    "Chennai", "Pune", "Kolkata", "Ahmedabad",
    "Jaipur", "Lucknow"
]

city_state_map = {
    "Delhi": "Delhi",
    "Mumbai": "Maharashtra",
    "Bengaluru": "Karnataka",
    "Hyderabad": "Telangana",
    "Chennai": "Tamil Nadu",
    "Pune": "Maharashtra",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan",
    "Lucknow": "Uttar Pradesh"
}

acquisition_channels = [
    "Organic Search",
    "Google Ads",
    "Instagram",
    "Referral",
    "Email",
    "Direct"
]

channel_probabilities = [
    0.24,
    0.22,
    0.18,
    0.14,
    0.10,
    0.12
]


def random_date(start, end):
    days_difference = (end - start).days
    random_days = random.randint(0, days_difference)
    return start + timedelta(days=random_days)


customers = []

for i in range(1, NUM_CUSTOMERS + 1):

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    city = random.choice(cities)

    acquisition_channel = np.random.choice(
        acquisition_channels,
        p=channel_probabilities
    )

    signup_date = random_date(
        START_DATE,
        END_DATE
    )

    customer = {
        "customer_id": f"CUST{i:05d}",
        "customer_name": f"{first_name} {last_name}",
        "age": random.randint(18, 65),
        "gender": random.choice(
            ["Male", "Female", "Other"]
        ),
        "city": city,
        "state": city_state_map[city],
        "country": "India",
        "signup_date": signup_date.date(),
        "acquisition_channel": acquisition_channel
    }

    customers.append(customer)


customers_df = pd.DataFrame(customers)

customers_df.to_csv(
    DATA_DIR / "customers.csv",
    index=False
)

print(
    f"Generated {len(customers_df)} customers"
)



# -----------------------------
# PRODUCT DATA
# -----------------------------

categories = {
    "Electronics": [
        "Laptops",
        "Mobiles",
        "Accessories",
        "Audio"
    ],
    "Home & Furniture": [
        "Furniture",
        "Kitchen",
        "Decor",
        "Storage"
    ],
    "Fashion": [
        "Men",
        "Women",
        "Footwear",
        "Accessories"
    ],
    "Beauty": [
        "Skincare",
        "Haircare",
        "Makeup",
        "Fragrance"
    ],
    "Sports": [
        "Fitness",
        "Outdoor",
        "Sportswear",
        "Equipment"
    ]
}

suppliers = [
    "Nova Retail",
    "Urban Supply Co",
    "Prime Distributors",
    "Vertex Traders",
    "BluePeak Wholesale",
    "Metro Commerce"
]

products = []

for i in range(1, NUM_PRODUCTS + 1):

    category = random.choice(
        list(categories.keys())
    )

    subcategory = random.choice(
        categories[category]
    )

    price_ranges = {
        "Electronics": (2000, 50000),
        "Home & Furniture": (500, 25000),
        "Fashion": (300, 8000),
        "Beauty": (200, 5000),
        "Sports": (400, 15000)
    }

    min_price, max_price = price_ranges[category]

    cost_price = round(
        random.uniform(min_price, max_price),
        2
    )

    markup_pct = random.uniform(
        0.20,
        0.60
    )

    selling_price = round(
        cost_price * (1 + markup_pct),
        2
    )

    product = {
        "product_id": f"PROD{i:04d}",
        "product_name": f"{subcategory} Product {i}",
        "category": category,
        "subcategory": subcategory,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "supplier": random.choice(suppliers)
    }

    products.append(product)


products_df = pd.DataFrame(products)

products_df.to_csv(
    DATA_DIR / "products.csv",
    index=False
)

print(
    f"Generated {len(products_df)} products"
)

# -----------------------------
# ORDER DATA
# -----------------------------

order_statuses = (
    ["Delivered"] * 9
    + ["Cancelled"]
)

payment_methods = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Cash on Delivery"
]

discount_options = [
    0.00,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30
]

discount_probabilities = [
    0.20,
    0.20,
    0.22,
    0.16,
    0.12,
    0.07,
    0.03
]

orders = []
order_items = []

order_item_counter = 1


# Pre-create customer IDs for faster sampling
customer_ids = customers_df[
    "customer_id"
].tolist()

customer_signup_map = dict(
    zip(
        customers_df["customer_id"],
        pd.to_datetime(
            customers_df["signup_date"]
        )
    )
)


for i in range(1, NUM_ORDERS + 1):

    # -----------------------------
    # SELECT CUSTOMER
    # -----------------------------

    customer_id = random.choice(
        customer_ids
    )

    signup_date = (
        customer_signup_map[
            customer_id
        ].to_pydatetime()
    )


    # Order cannot happen before signup
    order_date = random_date(
        signup_date,
        END_DATE
    )


    # Initially only Delivered or Cancelled
    order_status = random.choice(
        order_statuses
    )


    shipping_cost = round(
        random.uniform(40, 250),
        2
    )


    order = {
        "order_id": f"ORD{i:06d}",
        "customer_id": customer_id,
        "order_date": order_date.date(),
        "order_status": order_status,
        "payment_method": random.choice(
            payment_methods
        ),
        "shipping_cost": shipping_cost
    }


    orders.append(order)


    # -----------------------------
    # ORDER ITEMS
    # -----------------------------

    # Each order contains 1-5 products
    num_items = random.randint(
        1,
        5
    )


    selected_products = (
        products_df.sample(
            num_items
        )
    )


    for _, product in (
        selected_products.iterrows()
    ):

        quantity = random.randint(
            1,
            3
        )


        discount_pct = (
            np.random.choice(
                discount_options,
                p=discount_probabilities
            )
        )


        order_item = {
            "order_item_id":
                f"ITEM{order_item_counter:07d}",

            "order_id":
                order["order_id"],

            "product_id":
                product["product_id"],

            "quantity":
                quantity,

            "unit_price":
                product["selling_price"],

            "discount_pct":
                discount_pct
        }


        order_items.append(
            order_item
        )

        order_item_counter += 1


# -----------------------------
# CREATE DATAFRAMES
# -----------------------------

orders_df = pd.DataFrame(
    orders
)

order_items_df = pd.DataFrame(
    order_items
)


print(
    f"Generated {len(orders_df)} orders"
)

print(
    f"Generated {len(order_items_df)} order items"
)


# -----------------------------
# RETURN DATA
# -----------------------------

return_reasons = [
    "Damaged",
    "Wrong Item",
    "Quality Issue",
    "Changed Mind",
    "Late Delivery",
    "Size/Fit"
]


category_return_rates = {
    "Electronics": 0.08,
    "Home & Furniture": 0.10,
    "Fashion": 0.18,
    "Beauty": 0.06,
    "Sports": 0.09
}

# Category-specific return reason distributions.
# Each set of probabilities sums to 1.0.
return_reason_probabilities = {
    "Fashion": {
        "Size/Fit": 0.42,
        "Changed Mind": 0.18,
        "Quality Issue": 0.14,
        "Damaged": 0.08,
        "Wrong Item": 0.08,
        "Late Delivery": 0.10
    },
    "Electronics": {
        "Damaged": 0.20,
        "Wrong Item": 0.10,
        "Quality Issue": 0.32,
        "Changed Mind": 0.14,
        "Late Delivery": 0.20,
        "Size/Fit": 0.04
    },
    "Home & Furniture": {
        "Damaged": 0.30,
        "Wrong Item": 0.10,
        "Quality Issue": 0.20,
        "Changed Mind": 0.12,
        "Late Delivery": 0.24,
        "Size/Fit": 0.04
    },
    "Beauty": {
        "Damaged": 0.12,
        "Wrong Item": 0.14,
        "Quality Issue": 0.30,
        "Changed Mind": 0.22,
        "Late Delivery": 0.18,
        "Size/Fit": 0.04
    },
    "Sports": {
        "Damaged": 0.15,
        "Wrong Item": 0.10,
        "Quality Issue": 0.25,
        "Changed Mind": 0.18,
        "Late Delivery": 0.17,
        "Size/Fit": 0.15
    }
}


returns = []

return_counter = 1


# -----------------------------
# BUILD RETURN BASE DATA
# -----------------------------

# Add product category
return_base_df = (
    order_items_df.merge(
        products_df[
            [
                "product_id",
                "category"
            ]
        ],
        on="product_id",
        how="left"
    )
)


# Add order information
return_base_df = (
    return_base_df.merge(
        orders_df[
            [
                "order_id",
                "order_date",
                "order_status"
            ]
        ],
        on="order_id",
        how="left"
    )
)


# -----------------------------
# GENERATE RETURNS
# -----------------------------

for _, item in (
    return_base_df.iterrows()
):

    # Cancelled orders cannot be returned
    if (
        item["order_status"]
        == "Cancelled"
    ):
        continue


    category = item[
        "category"
    ]


    return_probability = (
        category_return_rates[
            category
        ]
    )


    # Decide whether item is returned
    if random.random() < return_probability:

        order_date = pd.to_datetime(
            item["order_date"]
        )

        # Return occurs 3-30 days after order
        return_date = (
            order_date
            + timedelta(
                days=random.randint(3, 30)
            )
        )

        # Keep return within dataset period
        return_date = min(
            return_date,
            pd.Timestamp(END_DATE)
        )

        refund_amount = round(
            item["quantity"]
            * item["unit_price"]
            * (1 - item["discount_pct"]),
            2
        )

        # Choose a category-specific return reason
        reason_distribution = (
            return_reason_probabilities[category]
        )

        return_reason = np.random.choice(
            list(reason_distribution.keys()),
            p=list(reason_distribution.values())
        )

        return_record = {
            "return_id": f"RET{return_counter:06d}",
            "order_item_id": item["order_item_id"],
            "return_date": return_date.date(),
            "return_reason": return_reason,
            "refund_amount": refund_amount
        }

        returns.append(return_record)
        return_counter += 1


# -----------------------------
# CREATE RETURNS DATAFRAME
# -----------------------------

returns_df = pd.DataFrame(
    returns
)


# -----------------------------
# UPDATE ORDER STATUS
# -----------------------------

# Find order IDs that actually
# contain returned items

returned_item_ids = set(
    returns_df[
        "order_item_id"
    ]
)


returned_order_ids = set(
    order_items_df[
        order_items_df[
            "order_item_id"
        ].isin(
            returned_item_ids
        )
    ][
        "order_id"
    ]
)


# Only now mark those orders
# as Returned

orders_df.loc[
    orders_df[
        "order_id"
    ].isin(
        returned_order_ids
    ),
    "order_status"
] = "Returned"


# -----------------------------
# SAVE FILES
# -----------------------------

orders_df.to_csv(
    DATA_DIR / "orders.csv",
    index=False
)

order_items_df.to_csv(
    DATA_DIR / "order_items.csv",
    index=False
)

returns_df.to_csv(
    DATA_DIR / "returns.csv",
    index=False
)


print(
    f"Generated {len(returns_df)} returns"
)


# -----------------------------
# QUICK VALIDATION
# -----------------------------

cancelled_orders = set(
    orders_df.loc[
        orders_df[
            "order_status"
        ] == "Cancelled",
        "order_id"
    ]
)


returned_orders = set(
    order_items_df.loc[
        order_items_df[
            "order_item_id"
        ].isin(
            returned_item_ids
        ),
        "order_id"
    ]
)


invalid_returned_cancelled = (
    cancelled_orders
    .intersection(
        returned_orders
    )
)


print(
    "Returns on cancelled orders:",
    len(
        invalid_returned_cancelled
    )
)


print(
    "\nFinal order status distribution:"
)

print(
    orders_df[
        "order_status"
    ].value_counts()
)


# -----------------------------
# WEBSITE SESSION DATA
# -----------------------------

NUM_SESSIONS = 200000

devices = [
    "Mobile",
    "Desktop",
    "Tablet"
]

device_probabilities = [
    0.62,
    0.30,
    0.08
]

traffic_sources = [
    "Organic Search",
    "Google Ads",
    "Instagram",
    "Referral",
    "Email",
    "Direct"
]

traffic_probabilities = [
    0.25,
    0.22,
    0.20,
    0.10,
    0.10,
    0.13
]


# Create lookup structures once
# This is much faster than repeatedly searching customers_df
customer_ids = customers_df["customer_id"].tolist()

customer_signup_map = dict(
    zip(
        customers_df["customer_id"],
        pd.to_datetime(customers_df["signup_date"])
    )
)


website_sessions = []


for i in range(1, NUM_SESSIONS + 1):

    # ---------------------------------
    # CUSTOMER + SESSION DATE
    # ---------------------------------

    # 70% sessions belong to registered customers
    if random.random() < 0.70:

        customer_id = random.choice(customer_ids)

        customer_signup_date = (
            customer_signup_map[customer_id]
            .to_pydatetime()
        )

        # Registered customer's session cannot
        # occur before signup
        session_date = random_date(
            customer_signup_date,
            END_DATE
        )

    # 30% are anonymous visitors
    else:

        customer_id = None

        # Anonymous visitors may appear
        # anywhere in the dataset period
        session_date = random_date(
            START_DATE,
            END_DATE
        )


    # ---------------------------------
    # DEVICE
    # ---------------------------------

    device = np.random.choice(
        devices,
        p=device_probabilities
    )


    # ---------------------------------
    # TRAFFIC SOURCE
    # ---------------------------------

    traffic_source = np.random.choice(
        traffic_sources,
        p=traffic_probabilities
    )


    # ---------------------------------
    # ENGAGEMENT
    # ---------------------------------

    pages_viewed = random.randint(
        1,
        15
    )

    session_duration = random.randint(
        20,
        1200
    )


    # Users viewing more pages have
    # higher probability of adding to cart
    add_cart_probability = min(
        0.10 + pages_viewed * 0.025,
        0.60
    )


    added_to_cart = (
        random.random()
        < add_cart_probability
    )


    # ---------------------------------
    # CONVERSION PROBABILITY
    # ---------------------------------

    device_conversion_rates = {
        "Mobile": 0.045,
        "Desktop": 0.085,
        "Tablet": 0.055
    }


    conversion_probability = (
        device_conversion_rates[device]
    )


    # Adding to cart strongly
    # increases conversion probability
    if added_to_cart:
        conversion_probability += 0.20


    # Certain channels perform better
    if traffic_source == "Email":
        conversion_probability += 0.04

    elif traffic_source == "Referral":
        conversion_probability += 0.03


    # Ensure probability never exceeds 100%
    conversion_probability = min(
        conversion_probability,
        1.0
    )


    converted = (
        random.random()
        < conversion_probability
    )


    # ---------------------------------
    # CREATE SESSION ROW
    # ---------------------------------

    session = {
        "session_id": f"SES{i:07d}",
        "customer_id": customer_id,
        "session_date": session_date.date(),
        "device": device,
        "traffic_source": traffic_source,
        "pages_viewed": pages_viewed,
        "session_duration_seconds": session_duration,
        "added_to_cart": int(added_to_cart),
        "converted": int(converted)
    }


    website_sessions.append(session)


# ---------------------------------
# CREATE DATAFRAME
# ---------------------------------

sessions_df = pd.DataFrame(
    website_sessions
)


# ---------------------------------
# SAVE CSV
# ---------------------------------

sessions_df.to_csv(
    DATA_DIR / "website_sessions.csv",
    index=False
)


print(
    f"Generated {len(sessions_df)} website sessions"
)


# ---------------------------------
# QUICK VALIDATION
# ---------------------------------

registered_sessions = sessions_df[
    sessions_df["customer_id"].notna()
].copy()

registered_sessions["signup_date"] = (
    registered_sessions["customer_id"]
    .map(customer_signup_map)
)

registered_sessions["session_date"] = (
    pd.to_datetime(
        registered_sessions["session_date"]
    )
)

invalid_sessions = registered_sessions[
    registered_sessions["session_date"]
    <
    registered_sessions["signup_date"]
]

print(
    "Sessions before customer signup:",
    len(invalid_sessions)
)


# -----------------------------
# MARKETING CAMPAIGNS
# -----------------------------

NUM_CAMPAIGNS = 80

campaign_channels = [
    "Google Ads",
    "Instagram",
    "Facebook",
    "Email",
    "YouTube",
    "Influencer"
]

campaign_types = [
    "Brand Awareness",
    "Product Launch",
    "Seasonal Sale",
    "Retargeting",
    "Customer Acquisition"
]

marketing_campaigns = []


for i in range(1, NUM_CAMPAIGNS + 1):

    channel = random.choice(
        campaign_channels
    )

    campaign_type = random.choice(
        campaign_types
    )


    start_date = random_date(
        START_DATE,
        END_DATE - timedelta(days=60)
    )


    campaign_length = random.randint(
        30,
        120
    )


    end_date = start_date + timedelta(
        days=campaign_length
    )


    if end_date > END_DATE:
        end_date = END_DATE


    budget = round(
        random.uniform(
            50000,
            800000
        ),
        2
    )


    campaign = {
        "campaign_id": f"CAMP{i:04d}",
        "campaign_name":
            f"{campaign_type} {i}",
        "channel": channel,
        "campaign_type": campaign_type,
        "start_date": start_date.date(),
        "end_date": end_date.date(),
        "campaign_budget": budget
    }


    marketing_campaigns.append(
        campaign
    )


campaigns_df = pd.DataFrame(
    marketing_campaigns
)


campaigns_df.to_csv(
    DATA_DIR / "marketing_campaigns.csv",
    index=False
)


print(
    f"Generated {len(campaigns_df)} marketing campaigns"
)



# -----------------------------
# CAMPAIGN PERFORMANCE
# -----------------------------

campaign_performance = []

performance_counter = 1


channel_ctr = {
    "Google Ads": 0.045,
    "Instagram": 0.030,
    "Facebook": 0.025,
    "Email": 0.075,
    "YouTube": 0.018,
    "Influencer": 0.035
}


channel_conversion_rates = {
    "Google Ads": 0.055,
    "Instagram": 0.040,
    "Facebook": 0.035,
    "Email": 0.085,
    "YouTube": 0.025,
    "Influencer": 0.050
}


channel_order_values = {
    "Google Ads": 2800,
    "Instagram": 2200,
    "Facebook": 2100,
    "Email": 3200,
    "YouTube": 2500,
    "Influencer": 2700
}


for _, campaign in campaigns_df.iterrows():

    campaign_id = campaign[
        "campaign_id"
    ]

    channel = campaign[
        "channel"
    ]

    start_date = pd.to_datetime(
        campaign["start_date"]
    )

    end_date = pd.to_datetime(
        campaign["end_date"]
    )

    campaign_budget = campaign[
        "campaign_budget"
    ]


    campaign_days = (
        end_date - start_date
    ).days + 1


    daily_budget = (
        campaign_budget
        / campaign_days
    )


    current_date = start_date


    while current_date <= end_date:

        # Daily spend varies slightly
        ad_spend = max(
            100,
            np.random.normal(
                daily_budget,
                daily_budget * 0.15
            )
        )


        # Approximate cost per thousand impressions
        cpm = random.uniform(
            80,
            250
        )


        impressions = int(
            (ad_spend / cpm) * 1000
        )


        base_ctr = channel_ctr[
            channel
        ]


        actual_ctr = max(
            0.005,
            np.random.normal(
                base_ctr,
                base_ctr * 0.12
            )
        )


        clicks = int(
            impressions * actual_ctr
        )


        conversion_rate = (
            channel_conversion_rates[
                channel
            ]
        )


        actual_conversion_rate = max(
            0.005,
            np.random.normal(
                conversion_rate,
                conversion_rate * 0.15
            )
        )


        conversions = int(
            clicks
            * actual_conversion_rate
        )


        avg_order_value = (
            channel_order_values[
                channel
            ]
        )


        revenue_generated = round(
            conversions
            * np.random.normal(
                avg_order_value,
                avg_order_value * 0.15
            ),
            2
        )


        performance = {
            "performance_id":
                f"PERF{performance_counter:07d}",

            "campaign_id":
                campaign_id,

            "date":
                current_date.date(),

            "impressions":
                impressions,

            "clicks":
                clicks,

            "ad_spend":
                round(ad_spend, 2),

            "conversions":
                conversions,

            "revenue_generated":
                max(
                    revenue_generated,
                    0
                )
        }


        campaign_performance.append(
            performance
        )


        performance_counter += 1

        current_date += timedelta(
            days=1
        )


campaign_performance_df = pd.DataFrame(
    campaign_performance
)


campaign_performance_df.to_csv(
    DATA_DIR / "campaign_performance.csv",
    index=False
)


print(
    f"Generated {len(campaign_performance_df)} campaign performance records"
)