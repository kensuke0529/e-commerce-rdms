import pandas as pd 

def create_churn_features():
    """
    Complete feature engineering pipeline for churn prediction
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from sql_via_python import query_executor
    import pandas as pd
    
    # Combine all features
    combined_query = """
    WITH rfm_features AS (
        SELECT 
            c.customer_id,
            -- RFM Features
            EXTRACT(DAY FROM (DATE('2024-07-31') - MAX(oh.order_date))) as days_since_last_order,
            COUNT(oh.order_id) as total_orders,
            COALESCE(SUM(p.amount), 0) as total_spend,
            COALESCE(AVG(p.amount), 0) as avg_order_value,
            
            -- Churn Label (180 days threshold - more realistic)
            CASE 
                WHEN MAX(oh.order_date) IS NULL THEN 1  -- Never ordered = churned
                WHEN EXTRACT(DAY FROM (DATE('2024-07-31') - MAX(oh.order_date))) > 180 
                THEN 1 ELSE 0 
            END as churn_label
            
        FROM customer c
        LEFT JOIN order_header oh ON c.customer_id = oh.customer_id
        LEFT JOIN payment p ON oh.order_id = p.order_id
        GROUP BY c.customer_id
    ),
    
    product_features AS (
        SELECT 
            c.customer_id,
            COUNT(DISTINCT p.category) as categories_purchased,
            COALESCE(AVG(p.product_price), 0) as avg_product_price,
            COUNT(DISTINCT p.product_id) as unique_products
        FROM customer c
        LEFT JOIN order_header oh ON c.customer_id = oh.customer_id
        LEFT JOIN product p ON oh.product_id = p.product_id
        GROUP BY c.customer_id
    ),
    
    engagement_features AS (
        SELECT 
            c.customer_id,
            COUNT(b.bid_id) as total_bids,
            COUNT(cr.review_id) as reviews_given,
            COUNT(cs.cservice_id) as support_tickets
        FROM customer c
        LEFT JOIN bid b ON c.customer_id = b.customer_id
        LEFT JOIN customer_review cr ON c.customer_id = cr.customer_id
        LEFT JOIN customer_service cs ON c.customer_id = cs.customer_id
        GROUP BY c.customer_id
    )
    
    SELECT 
        r.customer_id,
        r.days_since_last_order,
        r.total_orders,
        r.total_spend,
        r.avg_order_value,
        r.churn_label,
        pf.categories_purchased,
        pf.avg_product_price,
        pf.unique_products,
        ef.total_bids,
        ef.reviews_given,
        ef.support_tickets,
        
        -- Derived features
        CASE WHEN r.total_orders = 0 THEN 0 ELSE r.total_spend / r.total_orders END as spend_per_order,
        CASE WHEN r.total_orders = 0 THEN 0 ELSE ef.total_bids / r.total_orders END as bids_per_order
        
    FROM rfm_features r
    LEFT JOIN product_features pf ON r.customer_id = pf.customer_id
    LEFT JOIN engagement_features ef ON r.customer_id = ef.customer_id
    ORDER BY r.customer_id;
    """
    
    # Execute query
    db = query_executor(combined_query)
    db.connect_to_db()
    results = db.execute()
    
    if results:
        columns = [desc[0] for desc in db.cur.description]
        df = pd.DataFrame(results, columns=columns)
        db.close()
        return df
    else:
        db.close()
        return pd.DataFrame()
    
def prepare_ml_dataset():
    """
    Complete ML dataset preparation
    """
    import pandas as pd
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    
    # Extract features
    df = create_churn_features()
    
    # Handle missing values
    df = df.fillna(0)
    
    # Feature selection
    feature_columns = [
        'days_since_last_order',
        'total_orders', 
        'total_spend',
        'avg_order_value',
        'categories_purchased',
        'avg_product_price',
        'unique_products',
        'total_bids',
        'reviews_given',
        'support_tickets',
        'spend_per_order',
        'bids_per_order'
    ]
    
    X = df[feature_columns]
    y = df['churn_label']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_columns

if __name__ == "__main__":
    X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_columns = prepare_ml_dataset()
    
    # Convert scaled arrays back to DataFrames for easier viewing
    import pandas as pd
    X_train_df = pd.DataFrame(X_train_scaled, columns=feature_columns)
    X_test_df = pd.DataFrame(X_test_scaled, columns=feature_columns)
    
    print("Scaled Training Data Shape:", X_train_scaled.shape)
    print("Scaled Test Data Shape:", X_test_scaled.shape)
    print("\nFirst 5 rows of scaled training data:")
    print(X_train_df.head())
    print("\nTarget distribution:")
    print(y_train.value_counts())