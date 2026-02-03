"""
PostgreSQL to ClickHouse Ingestion using clickhouse_connect library.

This module provides data ingestion from PostgreSQL to ClickHouse 
with features like:
- Direct connection to ClickHouse Cloud (HTTPS)
- Batch processing with configurable batch size
- Checkpoint/resume capability for large datasets
- Automatic table creation from PostgreSQL schema

Usage:
    python pg_to_clickhouse.py

Requirements:
    pip install clickhouse-connect psycopg2-binary python-dotenv pandas
"""

import os
import json
import pandas as pd
import clickhouse_connect
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Batch size for processing
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))

# Checkpoint file
CHECKPOINT_FILE = "ch_ingestion_checkpoint.json"


def get_postgres_engine():
    """Create PostgreSQL SQLAlchemy engine from environment variables."""
    host = os.getenv("PG_HOST", "localhost")
    database = os.getenv("PG_DATABASE", "mydb")
    user = os.getenv("PG_USER", "myuser")
    password = os.getenv("PG_PASSWORD", "mypassword")
    port = os.getenv("PG_PORT", "5432")
    
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(conn_string)


def get_clickhouse_client():
    """
    Create ClickHouse client using clickhouse_connect.
    
    Supports both local ClickHouse and ClickHouse Cloud (HTTPS).
    """
    host = os.getenv("CH_HOST", "localhost")
    port = int(os.getenv("CH_PORT", "8443"))
    database = os.getenv("CH_DATABASE", "default")
    username = os.getenv("CH_USER", "default")
    password = os.getenv("CH_PASSWORD", "")
    secure = os.getenv("CH_SECURE", "1") == "1"
    
    print(f"📋 ClickHouse Connection:")
    print(f"   Host: {host}:{port}")
    print(f"   Database: {database}")
    print(f"   User: {username}")
    print(f"   Secure: {secure}")
    
    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        secure=secure,
        # Connection settings for reliability
        connect_timeout=30,
        send_receive_timeout=300,
    )
    
    # Verify connection
    version = client.command("SELECT version()")
    print(f"   ✅ Connected to ClickHouse {version}")
    
    return client


def save_checkpoint(checkpoint_data):
    """Save checkpoint to file for resumable ingestion."""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)
    print(f"   💾 Checkpoint saved: batch {checkpoint_data['last_completed_batch'] + 1}")


def load_checkpoint(table_name):
    """Load checkpoint from file if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)
        if checkpoint.get('table_name') == table_name:
            print(f"   📂 Checkpoint found: resuming from batch {checkpoint['last_completed_batch'] + 2}")
            return checkpoint
    return None


def clear_checkpoint():
    """Remove checkpoint file after successful completion."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print(f"   🧹 Checkpoint file cleared")


def pg_type_to_ch_type(pg_type: str) -> str:
    """Convert PostgreSQL data type to ClickHouse data type."""
    pg_type = str(pg_type).upper()
    
    type_mapping = {
        'INTEGER': 'Int32',
        'BIGINT': 'Int64',
        'SMALLINT': 'Int16',
        'SERIAL': 'Int32',
        'BIGSERIAL': 'Int64',
        'REAL': 'Float32',
        'DOUBLE PRECISION': 'Float64',
        'NUMERIC': 'Decimal(38, 10)',
        'DECIMAL': 'Decimal(38, 10)',
        'BOOLEAN': 'Bool',
        'VARCHAR': 'String',
        'CHARACTER VARYING': 'String',
        'CHAR': 'String',
        'TEXT': 'String',
        'DATE': 'Date',
        'TIMESTAMP': 'DateTime64(3)',
        'TIMESTAMP WITHOUT TIME ZONE': 'DateTime64(3)',
        'TIMESTAMP WITH TIME ZONE': 'DateTime64(3)',
        'TIME': 'String',
        'UUID': 'UUID',
        'JSON': 'String',
        'JSONB': 'String',
        'BYTEA': 'String',
        'INET': 'String',
        'CIDR': 'String',
        'MACADDR': 'String',
    }
    
    # Check for exact match first
    if pg_type in type_mapping:
        return type_mapping[pg_type]
    
    # Check for partial match (e.g., VARCHAR(255))
    for pg_key, ch_type in type_mapping.items():
        if pg_type.startswith(pg_key):
            return ch_type
    
    # Default to String for unknown types
    return 'String'


def get_create_table_sql(df: pd.DataFrame, table_name: str, pg_columns: dict = None) -> str:
    """Generate ClickHouse CREATE TABLE SQL from DataFrame schema."""
    columns = []
    
    for col in df.columns:
        if pg_columns and col in pg_columns:
            ch_type = pg_type_to_ch_type(pg_columns[col])
        else:
            # Infer from pandas dtype
            dtype = str(df[col].dtype)
            if 'int' in dtype:
                ch_type = 'Int64'
            elif 'float' in dtype:
                ch_type = 'Float64'
            elif 'bool' in dtype:
                ch_type = 'Bool'
            elif 'datetime' in dtype:
                ch_type = 'DateTime64(3)'
            else:
                ch_type = 'String'
        
        # Make all columns Nullable to handle NULL values
        columns.append(f"    `{col}` Nullable({ch_type})")
    
    columns_sql = ",\n".join(columns)
    
    create_sql = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
{columns_sql}
) ENGINE = MergeTree()
ORDER BY tuple()
"""
    return create_sql


def ingest_query_to_clickhouse(
    sql_query: str,
    target_table: str,
    batch_size: int = BATCH_SIZE,
    replace: bool = True
):
    """
    Ingest data from a PostgreSQL query to ClickHouse.
    
    Args:
        sql_query: SQL query to execute on PostgreSQL.
        target_table: Target table name in ClickHouse.
        batch_size: Number of rows per batch.
        replace: If True, drop and recreate table. If False, append data.
    
    Returns:
        Total rows inserted.
    """
    print("\n" + "=" * 60)
    print("🚀 Starting PostgreSQL to ClickHouse Ingestion")
    print("=" * 60 + "\n")
    
    # Step 1: Connect to PostgreSQL
    print("Step 1/5: Connecting to PostgreSQL...")
    pg_engine = get_postgres_engine()
    print(f"   ✅ Connected to PostgreSQL")
    
    # Step 2: Connect to ClickHouse
    print("\nStep 2/5: Connecting to ClickHouse...")
    ch_client = get_clickhouse_client()
    
    # Step 3: Count total rows
    print("\nStep 3/5: Counting total rows...")
    count_query = f"SELECT COUNT(*) as cnt FROM ({sql_query}) as subquery"
    with pg_engine.connect() as conn:
        result = conn.execute(text(count_query))
        total_rows = result.scalar()
    print(f"   ✅ Total rows to process: {total_rows:,}")
    
    if total_rows == 0:
        print("   ⚠️ No data to upload. Exiting.")
        return 0
    
    total_batches = (total_rows + batch_size - 1) // batch_size
    print(f"   Batch size: {batch_size:,}")
    print(f"   Total batches: {total_batches}")
    
    # Check for existing checkpoint
    checkpoint = load_checkpoint(target_table)
    start_batch = 0
    already_uploaded = 0
    
    if checkpoint and not replace:
        if (checkpoint.get('total_rows') == total_rows and
            checkpoint.get('batch_size') == batch_size):
            start_batch = checkpoint['last_completed_batch'] + 1
            already_uploaded = checkpoint.get('total_uploaded', start_batch * batch_size)
            print(f"   ✅ Resuming from batch {start_batch + 1}/{total_batches}")
        else:
            print("   ⚠️ Checkpoint mismatch, starting fresh")
            clear_checkpoint()
    
    # Step 4: Create/replace table if needed
    print("\nStep 4/5: Preparing ClickHouse table...")
    
    # Fetch first batch to get schema
    first_batch_query = f"{sql_query} LIMIT {batch_size}"
    with pg_engine.connect() as conn:
        first_df = pd.read_sql(text(first_batch_query), conn)
    
    if replace and start_batch == 0:
        # Drop existing table
        try:
            ch_client.command(f"DROP TABLE IF EXISTS {target_table}")
            print(f"   🗑️ Dropped existing table: {target_table}")
        except Exception as e:
            print(f"   ⚠️ Could not drop table: {e}")
        
        # Create table
        create_sql = get_create_table_sql(first_df, target_table)
        print(f"   📝 Creating table with schema:")
        for col, dtype in first_df.dtypes.items():
            print(f"      - {col}: {dtype}")
        
        ch_client.command(create_sql)
        print(f"   ✅ Table created: {target_table}")
    
    # Step 5: Process in batches
    print(f"\nStep 5/5: Processing data in batches...")
    total_uploaded = already_uploaded
    
    for batch_num in range(start_batch, total_batches):
        offset = batch_num * batch_size
        
        print(f"\n   📦 Batch {batch_num + 1}/{total_batches}")
        print(f"      Offset: {offset:,}, Limit: {batch_size:,}")
        
        # Fetch batch
        batch_query = f"{sql_query} LIMIT {batch_size} OFFSET {offset}"
        
        try:
            print(f"      Fetching from PostgreSQL...")
            with pg_engine.connect() as conn:
                df = pd.read_sql(text(batch_query), conn)
            
            rows_fetched = len(df)
            print(f"      ✅ Fetched {rows_fetched:,} rows")
            
            if df.empty:
                print(f"      ⚠️ Empty batch, skipping...")
                continue
            
            # Convert DataFrame to list of lists for insert
            print(f"      Inserting to ClickHouse...")
            
            # Handle NaN/NaT values - convert to None
            df = df.where(pd.notnull(df), None)
            
            # Insert using clickhouse_connect
            ch_client.insert(
                table=target_table,
                data=df.values.tolist(),
                column_names=df.columns.tolist()
            )
            
            total_uploaded += rows_fetched
            progress = (total_uploaded / total_rows) * 100
            print(f"      ✅ Inserted | Progress: {total_uploaded:,}/{total_rows:,} ({progress:.1f}%)")
            
            # Save checkpoint
            save_checkpoint({
                'table_name': target_table,
                'last_completed_batch': batch_num,
                'total_uploaded': total_uploaded,
                'total_rows': total_rows,
                'batch_size': batch_size
            })
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            print(f"      💾 Progress saved. Run again to resume from batch {batch_num + 1}")
            raise
    
    # Clear checkpoint on success
    clear_checkpoint()
    
    # Close client
    ch_client.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Ingestion complete!")
    print(f"   Total rows uploaded: {total_uploaded:,}")
    print(f"   Total batches: {total_batches}")
    print(f"   Target table: {target_table}")
    print("=" * 60 + "\n")
    
    return total_uploaded


def ingest_table_to_clickhouse(
    source_table: str,
    target_table: str = None,
    batch_size: int = BATCH_SIZE,
    replace: bool = True
):
    """
    Ingest a full PostgreSQL table to ClickHouse.
    
    Args:
        source_table: Source table name in PostgreSQL (can include schema, e.g., 'public.users').
        target_table: Target table name in ClickHouse. Defaults to source table name.
        batch_size: Number of rows per batch.
        replace: If True, drop and recreate table. If False, append data.
    
    Returns:
        Total rows inserted.
    """
    if target_table is None:
        # Use table name without schema
        target_table = source_table.split('.')[-1]
    
    sql_query = f"SELECT * FROM {source_table}"
    
    return ingest_query_to_clickhouse(
        sql_query=sql_query,
        target_table=target_table,
        batch_size=batch_size,
        replace=replace
    )


# --- Usage Example ---
if __name__ == "__main__":
    print("\n🔧 Initializing PostgreSQL to ClickHouse ingestion...\n")
    
    # Configuration from environment
    print(f"📋 Environment Configuration:")
    print(f"   PG_HOST: {os.getenv('PG_HOST')}")
    print(f"   PG_DATABASE: {os.getenv('PG_DATABASE')}")
    print(f"   CH_HOST: {os.getenv('CH_HOST')}")
    print(f"   CH_PORT: {os.getenv('CH_PORT', '8443')}")
    print(f"   CH_DATABASE: {os.getenv('CH_DATABASE', 'default')}")
    print(f"   CH_SECURE: {os.getenv('CH_SECURE', '1')}")
    print(f"   BATCH_SIZE: {BATCH_SIZE:,}")
    
    # Get SQL query from environment or use default
    SQL_QUERY = os.getenv("SQL_QUERY", "")
    TARGET_TABLE = os.getenv("CH_TARGET_TABLE", "view_trace_return")
    
    print(f"\n📝 Query: {SQL_QUERY}")
    print(f"   Target table: {TARGET_TABLE}")
    
    # Run ingestion
    ingest_query_to_clickhouse(
        sql_query=SQL_QUERY,
        target_table=TARGET_TABLE,
        batch_size=BATCH_SIZE,
        replace=True
    )
