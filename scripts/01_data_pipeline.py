"""
Hotel Booking Cancellation Analysis - Data Pipeline & Schema Normalization
Creates 4 relational tables:
1. customers (customer demographics, repeated guest status, customer type)
2. rooms (room types, matching status, meal plan)
3. channels (market segment, distribution channel, agent, company)
4. bookings (core transactional table with foreign keys, lead time, dates, deposit, adr, cancellation status)
Also creates SQLite database with relational integrity and exports CSVs.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split

def build_schema_and_tables(limit_records=15000):
    raw_path = 'data/raw/hotel_bookings.csv'
    df = pd.read_csv(raw_path)
    print(f"Loaded raw dataset with shape: {df.shape}")

    # Apply dataset limit (15,000 records) using stratified sampling to preserve hotel & cancellation proportions
    if limit_records and len(df) > limit_records:
        _, df = train_test_split(
            df,
            test_size=limit_records,
            stratify=df[['hotel', 'is_canceled']],
            random_state=42
        )
        df = df.reset_index(drop=True)
        print(f"Dataset limited to representative sample of {len(df)} records (stratified by hotel and is_canceled)")

    # Add unique primary identifier for bookings
    df['booking_id'] = ['BK_' + str(i + 100001) for i in range(len(df))]

    # Clean and standardize missing values
    df['children'] = df['children'].fillna(0).astype(int)
    df['country'] = df['country'].fillna('Unknown')
    df['agent'] = df['agent'].fillna(-1).astype(int).astype(str).replace('-1', 'None')
    df['company'] = df['company'].fillna(-1).astype(int).astype(str).replace('-1', 'None')

    # Derived business metrics
    df['total_nights'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
    df['total_guests'] = df['adults'] + df['children'] + df['babies']
    df['room_type_mismatch'] = (df['reserved_room_type'] != df['assigned_room_type']).astype(int)

    # 1. CUSTOMERS TABLE
    # Attributes relating to the customer profile
    customer_cols = [
        'booking_id', 'country', 'customer_type', 'is_repeated_guest',
        'previous_cancellations', 'previous_bookings_not_canceled',
        'adults', 'children', 'babies', 'total_guests'
    ]
    customers_df = df[customer_cols].copy()
    customers_df['customer_id'] = ['CUST_' + str(i + 200001) for i in range(len(customers_df))]
    # Reorder columns
    cust_ordered = ['customer_id', 'booking_id', 'country', 'customer_type', 
                    'is_repeated_guest', 'previous_cancellations', 
                    'previous_bookings_not_canceled', 'adults', 'children', 'babies', 'total_guests']
    customers_df = customers_df[cust_ordered]

    # Map customer_id back into df
    df['customer_id'] = customers_df['customer_id']

    # 2. CHANNELS TABLE
    # Attributes relating to booking acquisition channels and distribution
    channel_cols = ['booking_id', 'distribution_channel', 'market_segment', 'agent', 'company']
    channels_df = df[channel_cols].copy()
    channels_df['channel_id'] = ['CHN_' + str(i + 300001) for i in range(len(channels_df))]
    chn_ordered = ['channel_id', 'booking_id', 'distribution_channel', 'market_segment', 'agent', 'company']
    channels_df = channels_df[chn_ordered]
    df['channel_id'] = channels_df['channel_id']

    # 3. ROOMS TABLE
    # Attributes relating to accommodation, room assignment, and meal plans
    room_cols = ['booking_id', 'reserved_room_type', 'assigned_room_type', 'room_type_mismatch', 'meal']
    rooms_df = df[room_cols].copy()
    rooms_df['room_id'] = ['RM_' + str(i + 400001) for i in range(len(rooms_df))]
    rm_ordered = ['room_id', 'booking_id', 'reserved_room_type', 'assigned_room_type', 'room_type_mismatch', 'meal']
    rooms_df = rooms_df[rm_ordered]
    df['room_id'] = rooms_df['room_id']

    # 4. BOOKINGS TABLE
    # Core operational booking transaction table
    booking_cols = [
        'booking_id', 'customer_id', 'channel_id', 'room_id',
        'hotel', 'is_canceled', 'lead_time', 'arrival_date_year',
        'arrival_date_month', 'arrival_date_week_number', 'arrival_date_day_of_month',
        'stays_in_weekend_nights', 'stays_in_week_nights', 'total_nights',
        'deposit_type', 'days_in_waiting_list', 'booking_changes',
        'adr', 'required_car_parking_spaces', 'total_of_special_requests',
        'reservation_status', 'reservation_status_date'
    ]
    bookings_df = df[booking_cols].copy()

    # Save processed CSVs
    processed_dir = 'data/processed'
    os.makedirs(processed_dir, exist_ok=True)
    customers_df.to_csv(os.path.join(processed_dir, 'customers.csv'), index=False)
    channels_df.to_csv(os.path.join(processed_dir, 'channels.csv'), index=False)
    rooms_df.to_csv(os.path.join(processed_dir, 'rooms.csv'), index=False)
    bookings_df.to_csv(os.path.join(processed_dir, 'bookings.csv'), index=False)
    df.to_csv(os.path.join(processed_dir, 'hotel_bookings_master.csv'), index=False)
    print("Exported 4 normalized tables to data/processed/")

    # Build SQLite relational database
    db_path = 'database/hotel_cancellations.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        booking_id TEXT,
        country TEXT,
        customer_type TEXT,
        is_repeated_guest INTEGER,
        previous_cancellations INTEGER,
        previous_bookings_not_canceled INTEGER,
        adults INTEGER,
        children INTEGER,
        babies INTEGER,
        total_guests INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE channels (
        channel_id TEXT PRIMARY KEY,
        booking_id TEXT,
        distribution_channel TEXT,
        market_segment TEXT,
        agent TEXT,
        company TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE rooms (
        room_id TEXT PRIMARY KEY,
        booking_id TEXT,
        reserved_room_type TEXT,
        assigned_room_type TEXT,
        room_type_mismatch INTEGER,
        meal TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE bookings (
        booking_id TEXT PRIMARY KEY,
        customer_id TEXT,
        channel_id TEXT,
        room_id TEXT,
        hotel TEXT,
        is_canceled INTEGER,
        lead_time INTEGER,
        arrival_date_year INTEGER,
        arrival_date_month TEXT,
        arrival_date_week_number INTEGER,
        arrival_date_day_of_month INTEGER,
        stays_in_weekend_nights INTEGER,
        stays_in_week_nights INTEGER,
        total_nights INTEGER,
        deposit_type TEXT,
        days_in_waiting_list INTEGER,
        booking_changes INTEGER,
        adr REAL,
        required_car_parking_spaces INTEGER,
        total_of_special_requests INTEGER,
        reservation_status TEXT,
        reservation_status_date TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
        FOREIGN KEY (channel_id) REFERENCES channels (channel_id),
        FOREIGN KEY (room_id) REFERENCES rooms (room_id)
    );
    """)

    customers_df.to_sql('customers', conn, if_exists='append', index=False)
    channels_df.to_sql('channels', conn, if_exists='append', index=False)
    rooms_df.to_sql('rooms', conn, if_exists='append', index=False)
    bookings_df.to_sql('bookings', conn, if_exists='append', index=False)

    conn.commit()
    conn.close()
    print("Database built and loaded into database/hotel_cancellations.db successfully!")

if __name__ == '__main__':
    build_schema_and_tables()
