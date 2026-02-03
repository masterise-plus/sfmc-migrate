import os
import json
import pandas as pd
import pandas_gbq
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()

# Batch size for processing
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))

# Checkpoint directory (supports parallel ingestion)
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", ".")


def get_checkpoint_filename(bq_dataset_table):
    """Generate unique checkpoint filename based on target table."""
    # Replace dots with underscores to create valid filename
    safe_name = bq_dataset_table.replace(".", "_")
    return os.path.join(CHECKPOINT_DIR, f"checkpoint_{safe_name}.json")


def save_checkpoint(checkpoint_data, bq_dataset_table):
    """Save checkpoint to file for resumable ingestion."""
    checkpoint_file = get_checkpoint_filename(bq_dataset_table)
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)
    print(f"   💾 Checkpoint saved: batch {checkpoint_data['last_completed_batch'] + 1} ({checkpoint_file})")


def load_checkpoint(bq_dataset_table):
    """Load checkpoint from file if exists."""
    checkpoint_file = get_checkpoint_filename(bq_dataset_table)
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        print(f"   📂 Checkpoint found: resuming from batch {checkpoint['last_completed_batch'] + 2}")
        print(f"      File: {checkpoint_file}")
        return checkpoint
    return None


def clear_checkpoint(bq_dataset_table):
    """Remove checkpoint file after successful completion."""
    checkpoint_file = get_checkpoint_filename(bq_dataset_table)
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print(f"   🧹 Checkpoint file cleared: {checkpoint_file}")

def get_pg_config():
    """Get PostgreSQL configuration from environment variables."""
    print("📋 Loading PostgreSQL configuration...")
    config = {
        "host": os.getenv("PG_HOST", "localhost"),
        "database": os.getenv("PG_DATABASE", "mydb"),
        "user": os.getenv("PG_USER", "myuser"),
        "password": os.getenv("PG_PASSWORD", "mypassword"),
        "port": os.getenv("PG_PORT", "5432"),
    }
    print(f"   Host: {config['host']}:{config['port']}")
    print(f"   Database: {config['database']}")
    print(f"   User: {config['user']}")
    return config

def get_pg_connection_string():
    """Build PostgreSQL connection string for SQLAlchemy."""
    print("🔗 Building PostgreSQL connection string...")
    config = get_pg_config()
    conn_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    print("   Connection string created (password hidden)")
    return conn_string

def get_bq_config():
    """Get BigQuery configuration from environment variables."""
    print("📋 Loading BigQuery configuration...")
    config = {
        "project_id": os.getenv("BQ_PROJECT_ID", "my-gcp-project"),
        "dataset": os.getenv("BQ_DATASET", "my_dataset"),
        "table": os.getenv("BQ_TABLE", "my_table"),
    }
    # Build full table reference: dataset.table
    config["dataset_table"] = f"{config['dataset']}.{config['table']}"
    
    print(f"   Project ID: {config['project_id']}")
    print(f"   Dataset: {config['dataset']}")
    print(f"   Table: {config['table']}")
    print(f"   Full path: {config['project_id']}.{config['dataset_table']}")
    return config

def validate_bq_table_name(dataset_table):
    """Validate BigQuery table name format."""
    if '.' not in dataset_table:
        raise ValueError(
            f"❌ Invalid table name: '{dataset_table}'\n"
            f"   Must be in format 'dataset.table' (e.g., 'my_dataset.my_table')\n"
            f"   Please set BQ_DATASET and BQ_TABLE in your .env file"
        )
    return True

def count_rows(engine, sql_query):
    """Count total rows for the given query."""
    print("\nStep 2/5: Counting total rows...")
    count_query = f"SELECT COUNT(*) as cnt FROM ({sql_query}) as subquery"
    with engine.connect() as conn:
        result = conn.execute(text(count_query))
        total_rows = result.scalar()
    print(f"   ✅ Total rows to process: {total_rows:,}")
    return total_rows

def ingest_pg_to_bq_auto(bq_project_id, bq_dataset_table, sql_query, batch_size=BATCH_SIZE):
    """
    Ingests data from Postgres to BigQuery with batching mechanism.
    Creates the table if it doesn't exist.
    
    Args:
        bq_project_id (str): GCP Project ID.
        bq_dataset_table (str): Target table in format 'dataset.table'.
        sql_query (str): SQL query to fetch data from Postgres.
        batch_size (int): Number of rows per batch.
    """
    print("\n" + "="*60)
    print("🚀 Starting PostgreSQL to BigQuery Ingestion (Batch Mode)")
    print("="*60 + "\n")
    
    # Validate table name format
    validate_bq_table_name(bq_dataset_table)
    
    # Step 1: Create SQLAlchemy engine
    print("Step 1/5: Creating database connection...")
    engine = create_engine(get_pg_connection_string())
    print("   ✅ SQLAlchemy engine created\n")
    
    # Step 2: Count total rows first
    total_rows = count_rows(engine, sql_query)
    
    if total_rows == 0:
        print("   ⚠️ No data to upload. Exiting.")
        return
    
    # Calculate total batches
    total_batches = (total_rows + batch_size - 1) // batch_size
    print(f"   Batch size: {batch_size:,}")
    print(f"   Total batches: {total_batches}")
    
    # Check for existing checkpoint (resume capability)
    checkpoint = load_checkpoint(bq_dataset_table)
    start_batch = 0
    already_uploaded = 0
    
    if checkpoint:
        # Validate checkpoint matches current job
        if (checkpoint.get('total_rows') == total_rows and
            checkpoint.get('batch_size') == batch_size):
            start_batch = checkpoint['last_completed_batch'] + 1
            already_uploaded = checkpoint.get('total_uploaded', start_batch * batch_size)
            print(f"   ✅ Resuming from batch {start_batch + 1}/{total_batches}")
            print(f"   📊 Already uploaded: {already_uploaded:,} rows")
        else:
            print("   ⚠️ Checkpoint mismatch (different job parameters), starting fresh")
            clear_checkpoint(bq_dataset_table)
    
    # Step 3: Process in batches
    print(f"\nStep 3/5: Processing data in batches...")
    total_uploaded = already_uploaded
    
    for batch_num in range(start_batch, total_batches):
        offset = batch_num * batch_size
        
        print(f"\n   📦 Batch {batch_num + 1}/{total_batches}")
        print(f"      Offset: {offset:,}, Limit: {batch_size:,}")
        
        # Fetch batch with LIMIT/OFFSET
        batch_query = f"{sql_query} LIMIT {batch_size} OFFSET {offset}"
        
        print(f"      Fetching data...")
        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(batch_query), conn)
        except Exception as e:
            print(f"      ❌ Error fetching data: {e}")
            print(f"      💾 Progress saved. Run the script again to resume from batch {batch_num + 1}")
            save_checkpoint({
                'last_completed_batch': batch_num - 1,
                'total_uploaded': total_uploaded,
                'total_rows': total_rows,
                'batch_size': batch_size,
                'bq_dataset_table': bq_dataset_table,
                'bq_project_id': bq_project_id
            }, bq_dataset_table)
            raise
        
        rows_fetched = len(df)
        print(f"      ✅ Fetched {rows_fetched:,} rows")
        
        if df.empty:
            print(f"      ⚠️ Empty batch, skipping...")
            continue
        
        # Show schema on first batch only (or first batch after resume)
        if batch_num == start_batch:
            print(f"\n   📊 Schema detected (from current batch):")
            for col, dtype in df.dtypes.items():
                print(f"      - {col}: {dtype}")
        
        # Step 4: Upload batch to BigQuery using pandas_gbq
        print(f"      Uploading to BigQuery...")
        
        try:
            pandas_gbq.to_gbq(
                dataframe=df,
                destination_table=bq_dataset_table,
                project_id=bq_project_id,
                if_exists='append',  # Creates table if not exists, appends if exists
                progress_bar=False   # Disable progress bar for cleaner batch output
            )
        except Exception as e:
            print(f"      ❌ Error uploading to BigQuery: {e}")
            print(f"      💾 Progress saved. Run the script again to resume from batch {batch_num + 1}")
            save_checkpoint({
                'last_completed_batch': batch_num - 1,
                'total_uploaded': total_uploaded,
                'total_rows': total_rows,
                'batch_size': batch_size,
                'bq_dataset_table': bq_dataset_table,
                'bq_project_id': bq_project_id
            }, bq_dataset_table)
            raise
        
        total_uploaded += rows_fetched
        progress = (total_uploaded / total_rows) * 100
        print(f"      ✅ Batch uploaded | Progress: {total_uploaded:,}/{total_rows:,} ({progress:.1f}%)")
        
        # Save checkpoint after each successful batch
        save_checkpoint({
            'last_completed_batch': batch_num,
            'total_uploaded': total_uploaded,
            'total_rows': total_rows,
            'batch_size': batch_size,
            'bq_dataset_table': bq_dataset_table,
            'bq_project_id': bq_project_id
        }, bq_dataset_table)
    
    # Clear checkpoint on successful completion
    clear_checkpoint(bq_dataset_table)
    
    # Step 5: Summary
    print("\n" + "="*60)
    print("✅ Ingestion complete!")
    print(f"   Total rows uploaded: {total_uploaded:,}")
    print(f"   Total batches processed: {total_batches}")
    print(f"   Destination: {bq_project_id}.{bq_dataset_table}")
    print("="*60 + "\n")

# --- Usage Example ---
if __name__ == "__main__":
    print("\n🔧 Initializing ingestion script (Batch Mode)...\n")
    
    # Load config from environment variables
    BQ_CONFIG = get_bq_config()
    
    # SQL query can also be loaded from env if needed
    SQL_QUERY = os.getenv("SQL_QUERY", "SELECT * FROM public.users WHERE created_at > '2024-01-01'")
    print(f"\n📝 SQL Query loaded from environment")
    print(f"   Batch size: {BATCH_SIZE:,} rows")
    
    # Needs Google Cloud credentials set in environment:
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"🔑 Google credentials: {creds_path}")
    else:
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS not set (using default auth)")
    
    print("\n")
    
    ingest_pg_to_bq_auto(
        bq_project_id=BQ_CONFIG["project_id"],
        bq_dataset_table=BQ_CONFIG["dataset_table"],
        sql_query=SQL_QUERY,
        batch_size=BATCH_SIZE
    )
