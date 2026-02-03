# ClickHouse Connect Driver API | ClickHouse Docs
Note

Passing keyword arguments is recommended for most api methods given the number of possible arguments, most of which are optional.

_Methods not documented here are not considered part of the API, and may be removed or changed._

Client Initialization[​](#client-initialization "Direct link to Client Initialization")
---------------------------------------------------------------------------------------

The `clickhouse_connect.driver.client` class provides the primary interface between a Python application and the ClickHouse database server. Use the `clickhouse_connect.get_client` function to obtain a Client instance, which accepts the following arguments:

### Connection arguments[​](#connection-arguments "Direct link to Connection arguments")



* Parameter: interface
  * Type: str
  * Default: http
  * Description: Must be http or https.
* Parameter: host
  * Type: str
  * Default: localhost
  * Description: The hostname or IP address of the ClickHouse server. If not set, localhost will be used.
* Parameter: port
  * Type: int
  * Default: 8123 or 8443
  * Description: The ClickHouse HTTP or HTTPS port. If not set will default to 8123, or to 8443 if secure=True or interface=https.
* Parameter: username
  * Type: str
  * Default: default
  * Description: The ClickHouse user name. If not set, the default ClickHouse user will be used.
* Parameter: password
  * Type: str
  * Default: <empty string>
  * Description: The password for username.
* Parameter: database
  * Type: str
  * Default: None
  * Description: The default database for the connection. If not set, ClickHouse Connect will use the default database for username.
* Parameter: secure
  * Type: bool
  * Default: False
  * Description: Use HTTPS/TLS. This overrides inferred values from the interface or port arguments.
* Parameter: dsn
  * Type: str
  * Default: None
  * Description: A string in standard DSN (Data Source Name) format. Other connection values (such as host or user) will be extracted from this string if not set otherwise.
* Parameter: compress
  * Type: bool or str
  * Default: True
  * Description: Enable compression for ClickHouse HTTP inserts and query results. See Additional Options (Compression)
* Parameter: query_limit
  * Type: int
  * Default: 0 (unlimited)
  * Description: Maximum number of rows to return for any query response. Set this to zero to return unlimited rows. Note that large query limits may result in out of memory exceptions if results are not streamed, as all results are loaded into memory at once.
* Parameter: query_retries
  * Type: int
  * Default: 2
  * Description: Maximum number of retries for a query request. Only "retryable" HTTP responses will be retried. command or insert requests are not automatically retried by the driver to prevent unintended duplicate requests.
* Parameter: connect_timeout
  * Type: int
  * Default: 10
  * Description: HTTP connection timeout in seconds.
* Parameter: send_receive_timeout
  * Type: int
  * Default: 300
  * Description: Send/receive timeout for the HTTP connection in seconds.
* Parameter: client_name
  * Type: str
  * Default: None
  * Description: client_name prepended to the HTTP User Agent header. Set this to track client queries in the ClickHouse system.query_log.
* Parameter: pool_mgr
  * Type: obj
  * Default: <default PoolManager>
  * Description: The urllib3 library PoolManager to use. For advanced use cases requiring multiple connection pools to different hosts.
* Parameter: http_proxy
  * Type: str
  * Default: None
  * Description: HTTP proxy address (equivalent to setting the HTTP_PROXY environment variable).
* Parameter: https_proxy
  * Type: str
  * Default: None
  * Description: HTTPS proxy address (equivalent to setting the HTTPS_PROXY environment variable).
* Parameter: apply_server_timezone
  * Type: bool
  * Default: True
  * Description: Use server timezone for timezone aware query results. See Timezone Precedence
* Parameter: show_clickhouse_errors
  * Type: bool
  * Default: True
  * Description: Include detailed ClickHouse server error messages and exception codes in client exceptions.
* Parameter: autogenerate_session_id
  * Type: bool
  * Default: None
  * Description: Override the global autogenerate_session_id setting. If True, automatically generate a UUID4 session ID when none is provided.
* Parameter: proxy_path
  * Type: str
  * Default: <empty string>
  * Description: Optional path prefix to add to the ClickHouse server URL for proxy configurations.
* Parameter: form_encode_query_params
  * Type: bool
  * Default: False
  * Description: Send query parameters as form-encoded data in the request body instead of URL parameters. Useful for queries with large parameter sets that might exceed URL length limits.
* Parameter: rename_response_column
  * Type: str
  * Default: None
  * Description: Optional callback function or column name mapping to rename response columns in query results.


### HTTPS/TLS arguments[​](#httpstls-arguments "Direct link to HTTPS/TLS arguments")



* Parameter: verify
  * Type: bool
  * Default: True
  * Description: Validate the ClickHouse server TLS/SSL certificate (hostname, expiration, etc.) if using HTTPS/TLS.
* Parameter: ca_cert
  * Type: str
  * Default: None
  * Description: If verify=True, the file path to Certificate Authority root to validate ClickHouse server certificate, in .pem format. Ignored if verify is False. This is not necessary if the ClickHouse server certificate is a globally trusted root as verified by the operating system.
* Parameter: client_cert
  * Type: str
  * Default: None
  * Description: File path to a TLS Client certificate in .pem format (for mutual TLS authentication). The file should contain a full certificate chain, including any intermediate certificates.
* Parameter: client_cert_key
  * Type: str
  * Default: None
  * Description: File path to the private key for the Client Certificate. Required if the private key is not included the Client Certificate key file.
* Parameter: server_host_name
  * Type: str
  * Default: None
  * Description: The ClickHouse server hostname as identified by the CN or SNI of its TLS certificate. Set this to avoid SSL errors when connecting through a proxy or tunnel with a different hostname
* Parameter: tls_mode
  * Type: str
  * Default: None
  * Description: Controls advanced TLS behavior. proxy and strict do not invoke ClickHouse mutual TLS connection, but do send client cert and key.  mutual assumes ClickHouse mutual TLS auth with a client certificate.  None/default behavior is mutual


### Settings argument[​](#settings-argument "Direct link to Settings argument")

Finally, the `settings` argument to `get_client` is used to pass additional ClickHouse settings to the server for each client request. Note that in most cases, users with _readonly_\=_1_ access cannot alter settings sent with a query, so ClickHouse Connect will drop such settings in the final request and log a warning. The following settings apply only to HTTP queries/sessions used by ClickHouse Connect, and are not documented as general ClickHouse settings.



* Setting: buffer_size
  * Description: Buffer size (in bytes) used by the ClickHouse server before writing to the HTTP channel.
* Setting: session_id
  * Description: A unique session ID to associate related queries on the server. Required for temporary tables.
* Setting: compress
  * Description: Whether the ClickHouse server should compress the POST response data. This setting should only be used for "raw" queries.
* Setting: decompress
  * Description: Whether the data sent to the ClickHouse server must be decompressed. This setting should only be used for "raw" inserts.
* Setting: quota_key
  * Description: The quota key associated with this request. See the ClickHouse server documentation on quotas.
* Setting: session_check
  * Description: Used to check the session status.
* Setting: session_timeout
  * Description: Number of seconds of inactivity before the session identified by the session ID will time out and no longer be considered valid. Defaults to 60 seconds.
* Setting: wait_end_of_query
  * Description: Buffers the entire response on the ClickHouse server. This setting is required to return summary information, and is set automatically on non-streaming queries.
* Setting: role
  * Description: ClickHouse role to be used for the session. Valid transport setting that can be included in query context.


For other ClickHouse settings that can be sent with each query, see [the ClickHouse documentation](https://clickhouse.com/docs/operations/settings/settings).

### Client creation examples[​](#client-creation-examples "Direct link to Client creation examples")

*   Without any parameters, a ClickHouse Connect client will connect to the default HTTP port on `localhost` with the default user and no password:

```
import clickhouse_connect

client = clickhouse_connect.get_client()
print(client.server_version)
# Output: '22.10.1.98'

```


*   Connecting to a secure (HTTPS) external ClickHouse server

```
import clickhouse_connect

client = clickhouse_connect.get_client(host='play.clickhouse.com', secure=True, port=443, user='play', password='clickhouse')
print(client.command('SELECT timezone()'))
# Output: 'Etc/UTC'

```


*   Connecting with a session ID and other custom connection parameters and ClickHouse settings.

```
import clickhouse_connect

client = clickhouse_connect.get_client(
    host='play.clickhouse.com',
    user='play',
    password='clickhouse',
    port=443,
    session_id='example_session_1',
    connect_timeout=15,
    database='github',
    settings={'distributed_ddl_task_timeout':300},
)
print(client.database)
# Output: 'github'

```


Client Lifecycle and Best Practices[​](#client-lifecycle-and-best-practices "Direct link to Client Lifecycle and Best Practices")
---------------------------------------------------------------------------------------------------------------------------------

Creating a ClickHouse Connect client is an expensive operation that involves establishing a connection, retrieving server metadata, and initializing settings. Follow these best practices for optimal performance:

### Core principles[​](#core-principles "Direct link to Core principles")

*   **Reuse clients**: Create clients once at application startup and reuse them throughout the application lifetime
*   **Avoid frequent creation**: Don't create a new client for each query or request (this wastes hundreds of milliseconds per operation)
*   **Clean up properly**: Always close clients when shutting down to release connection pool resources
*   **Share when possible**: A single client can handle many concurrent queries through its connection pool (see threading notes below)

### Basic patterns[​](#basic-patterns "Direct link to Basic patterns")

**✅ Good: Reuse a single client**

```
import clickhouse_connect

# Create once at startup
client = clickhouse_connect.get_client(host='my-host', username='default', password='password')

# Reuse for all queries
for i in range(1000):
    result = client.query('SELECT count() FROM users')

# Close on shutdown
client.close()

```


**❌ Bad: Creating clients repeatedly**

```
# BAD: Creates 1000 clients with expensive initialization overhead
for i in range(1000):
    client = clickhouse_connect.get_client(host='my-host', username='default', password='password')
    result = client.query('SELECT count() FROM users')
    client.close()

```


### Multi-threaded applications[​](#multi-threaded-applications "Direct link to Multi-threaded applications")

Note

Client instances are **NOT thread-safe** when using session IDs. By default, clients have an auto-generated session ID, and concurrent queries within the same session will raise a `ProgrammingError`.

To share a client across threads safely:

```
import clickhouse_connect
import threading

# Option 1: Disable sessions (recommended for shared clients)
client = clickhouse_connect.get_client(
    host='my-host',
    username='default',
    password='password',
    autogenerate_session_id=False  # Required for thread safety
)

def worker(thread_id):
    # All threads can now safely use the same client
    result = client.query(f"SELECT {thread_id}")
    print(f"Thread {thread_id}: {result.result_rows[0][0]}")


threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

client.close()
# Output:
# Thread 0: 0
# Thread 7: 7
# Thread 1: 1
# Thread 9: 9
# Thread 4: 4
# Thread 2: 2
# Thread 8: 8
# Thread 5: 5
# Thread 6: 6
# Thread 3: 3

```


**Alternative for sessions:** If you need sessions (e.g., for temporary tables), create a separate client per thread:

```
def worker(thread_id):
    # Each thread gets its own client with isolated session
    client = clickhouse_connect.get_client(host='my-host', username='default', password='password')
    client.command('CREATE TEMPORARY TABLE temp (id UInt32) ENGINE = Memory')
    # ... use temp table ...
    client.close()

```


### Proper cleanup[​](#proper-cleanup "Direct link to Proper cleanup")

Always close clients at shutdown. Note that `client.close()` disposes the client and closes pooled HTTP connections only when the client owns its pool manager (for example, when created with custom TLS/proxy options). For the default shared pool, use `client.close_connections()` to proactively clear sockets; otherwise, connections are reclaimed automatically via idle expiration and at process exit.

```
client = clickhouse_connect.get_client(host='my-host', username='default', password='password')
try:
    result = client.query('SELECT 1')
finally:
    client.close()

```


Or use a context manager:

```
with clickhouse_connect.get_client(host='my-host', username='default', password='password') as client:
    result = client.query('SELECT 1')

```


### When to use multiple clients[​](#when-to-use-multiple-clients "Direct link to When to use multiple clients")

Multiple clients are appropriate for:

*   **Different servers**: One client per ClickHouse server or cluster
*   **Different credentials**: Separate clients for different users or access levels
*   **Different databases**: When you need to work with multiple databases
*   **Isolated sessions**: When you need separate sessions for temporary tables or session-specific settings
*   **Per-thread isolation**: When threads need independent sessions (as shown above)

Common method arguments[​](#common-method-arguments "Direct link to Common method arguments")
---------------------------------------------------------------------------------------------

Several client methods use one or both of the common `parameters` and `settings` arguments. These keyword arguments are described below.

### Parameters argument[​](#parameters-argument "Direct link to Parameters argument")

ClickHouse Connect Client `query*` and `command` methods accept an optional `parameters` keyword argument used for binding Python expressions to a ClickHouse value expression. Two sorts of binding are available.

#### Server-side binding[​](#server-side-binding "Direct link to Server-side binding")

ClickHouse supports [server side binding](about:/docs/interfaces/cli#cli-queries-with-parameters) for most query values, where the bound value is sent separate from the query as an HTTP query parameter. ClickHouse Connect will add the appropriate query parameters if it detects a binding expression of the form `{<name>:<datatype>}`. For server side binding, the `parameters` argument should be a Python dictionary.

*   Server-side binding with Python dictionary, DateTime value, and string value

```
import datetime

my_date = datetime.datetime(2022, 10, 1, 15, 20, 5)

parameters = {'table': 'my_table', 'v1': my_date, 'v2': "a string with a single quote'"}
client.query('SELECT * FROM {table:Identifier} WHERE date >= {v1:DateTime} AND string ILIKE {v2:String}', parameters=parameters)

```


This generates the following query on the server:

```
SELECT *
FROM my_table
WHERE date >= '2022-10-01 15:20:05'
  AND string ILIKE 'a string with a single quote\''

```


#### Client-side binding[​](#client-side-binding "Direct link to Client-side binding")

ClickHouse Connect also supports client-side parameter binding, which can allow more flexibility in generating templated SQL queries. For client-side binding, the `parameters` argument should be a dictionary or a sequence. Client-side binding uses the Python ["printf" style](https://docs.python.org/3/library/stdtypes.html#old-string-formatting) string formatting for parameter substitution.

Note that unlike server-side binding, client-side binding does not work for database identifiers such as database, table, or column names, since Python-style formatting cannot distinguish between the different types of strings, and they need to be formatted differently (backticks or double quotes for database identifiers, single quotes for data values).

*   Example with Python Dictionary, DateTime value and string escaping

```
import datetime

my_date = datetime.datetime(2022, 10, 1, 15, 20, 5)

parameters = {'v1': my_date, 'v2': "a string with a single quote'"}
client.query('SELECT * FROM my_table WHERE date >= %(v1)s AND string ILIKE %(v2)s', parameters=parameters)

```


This generates the following query on the server:

```
SELECT *
FROM my_table
WHERE date >= '2022-10-01 15:20:05'
  AND string ILIKE 'a string with a single quote\''

```


*   Example with Python Sequence (Tuple), Float64, and IPv4Address

```
import ipaddress

parameters = (35200.44, ipaddress.IPv4Address(0x443d04fe))
client.query('SELECT * FROM some_table WHERE metric >= %s AND ip_address = %s', parameters=parameters)

```


This generates the following query on the server:

```
SELECT *
FROM some_table
WHERE metric >= 35200.44
  AND ip_address = '68.61.4.254''

```


Note

To bind DateTime64 arguments (ClickHouse types with sub-second precision) requires one of two custom approaches:

*   Wrap the Python `datetime.datetime` value in the new DT64Param class, e.g.
    
    ```
  query = 'SELECT {p1:DateTime64(3)}'  # Server-side binding with dictionary
  parameters={'p1': DT64Param(dt_value)}

  query = 'SELECT %s as string, toDateTime64(%s,6) as dateTime' # Client-side binding with list 
  parameters=['a string', DT64Param(datetime.now())]

```

    
    *   If using a dictionary of parameter values, append the string `_64` to the parameter name
    
    ```
  query = 'SELECT {p1:DateTime64(3)}, {a1:Array(DateTime(3))}'  # Server-side binding with dictionary

  parameters={'p1_64': dt_value, 'a1_64': [dt_value1, dt_value2]}

```

    

### Settings argument[​](#settings-argument-1 "Direct link to Settings argument")

All the key ClickHouse Connect Client "insert" and "select" methods accept an optional `settings` keyword argument to pass ClickHouse server [user settings](https://clickhouse.com/docs/operations/settings/settings) for the included SQL statement. The `settings` argument should be a dictionary. Each item should be a ClickHouse setting name and its associated value. Note that values will be converted to strings when sent to the server as query parameters.

As with client level settings, ClickHouse Connect will drop any settings that the server marks as _readonly_\=_1_, with an associated log message. Settings that apply only to queries via the ClickHouse HTTP interface are always valid. Those settings are described under the `get_client` [API](#settings-argument).

Example of using ClickHouse settings:

```
settings = {'merge_tree_min_rows_for_concurrent_read': 65535,
            'session_id': 'session_1234',
            'use_skip_indexes': False}
client.query("SELECT event_type, sum(timeout) FROM event_errors WHERE event_time > '2022-08-01'", settings=settings)

```


Client `command` Method[​](#client-command-method "Direct link to client-command-method")
-----------------------------------------------------------------------------------------

Use the `Client.command` method to send SQL queries to the ClickHouse server that do not normally return data or that return a single primitive or array value rather than a full dataset. This method takes the following parameters:



* Parameter: cmd
  * Type: str
  * Default: Required
  * Description: A ClickHouse SQL statement that returns a single value or a single row of values.
* Parameter: parameters
  * Type: dict or iterable
  * Default: None
  * Description: See parameters description.
* Parameter: data
  * Type: str or bytes
  * Default: None
  * Description: Optional data to include with the command as the POST body.
* Parameter: settings
  * Type: dict
  * Default: None
  * Description: See settings description.
* Parameter: use_database
  * Type: bool
  * Default: True
  * Description: Use the client database (specified when creating the client). False means the command will use the default ClickHouse server database for the connected user.
* Parameter: external_data
  * Type: ExternalData
  * Default: None
  * Description: An ExternalData object containing file or binary data to use with the query. See Advanced Queries (External Data)


### Command examples[​](#command-examples "Direct link to Command examples")

#### DDL statements[​](#ddl-statements "Direct link to DDL statements")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Create a table
result = client.command("CREATE TABLE test_command (col_1 String, col_2 DateTime) ENGINE MergeTree ORDER BY tuple()")
print(result)  # Returns QuerySummary with query_id

# Show table definition
result = client.command("SHOW CREATE TABLE test_command")
print(result)
# Output:
# CREATE TABLE default.test_command
# (
#     `col_1` String,
#     `col_2` DateTime
# )
# ENGINE = MergeTree
# ORDER BY tuple()

# Drop table
client.command("DROP TABLE test_command")

```


#### Simple queries returning single values[​](#simple-queries-returning-single-values "Direct link to Simple queries returning single values")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Single value result
count = client.command("SELECT count() FROM system.tables")
print(count)
# Output: 151

# Server version
version = client.command("SELECT version()")
print(version)
# Output: "25.8.2.29"

```


#### Commands with parameters[​](#commands-with-parameters "Direct link to Commands with parameters")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Using client-side parameters
table_name = "system"
result = client.command(
    "SELECT count() FROM system.tables WHERE database = %(db)s",
    parameters={"db": table_name}
)

# Using server-side parameters
result = client.command(
    "SELECT count() FROM system.tables WHERE database = {db:String}",
    parameters={"db": "system"}
)

```


#### Commands with settings[​](#commands-with-settings "Direct link to Commands with settings")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Execute command with specific settings
result = client.command(
    "OPTIMIZE TABLE large_table FINAL",
    settings={"optimize_throw_if_noop": 1}
)

```


Client `query` Method[​](#client-query-method "Direct link to client-query-method")
-----------------------------------------------------------------------------------

The `Client.query` method is the primary way to retrieve a single "batch" dataset from the ClickHouse server. It utilizes the Native ClickHouse format over HTTP to transmit large datasets (up to approximately one million rows) efficiently. This method takes the following parameters:



* Parameter: query
  * Type: str
  * Default: Required
  * Description: The ClickHouse SQL SELECT or DESCRIBE query.
* Parameter: parameters
  * Type: dict or iterable
  * Default: None
  * Description: See parameters description.
* Parameter: settings
  * Type: dict
  * Default: None
  * Description: See settings description.
* Parameter: query_formats
  * Type: dict
  * Default: None
  * Description: Datatype formatting specification for result values. See Advanced Usage (Read Formats)
* Parameter: column_formats
  * Type: dict
  * Default: None
  * Description: Datatype formatting per column. See Advanced Usage (Read Formats)
* Parameter: encoding
  * Type: str
  * Default: None
  * Description: Encoding used to encode ClickHouse String columns into Python strings. Python defaults to UTF-8 if not set.
* Parameter: use_none
  * Type: bool
  * Default: True
  * Description: Use Python None type for ClickHouse nulls. If False, use a datatype default (such as 0) for ClickHouse nulls. Note - defaults to False for NumPy/Pandas for performance reasons.
* Parameter: column_oriented
  * Type: bool
  * Default: False
  * Description: Return the results as a sequence of columns rather than a sequence of rows. Helpful for transforming Python data to other column oriented data formats.
* Parameter: query_tz
  * Type: str
  * Default: None
  * Description: A timezone name from the zoneinfo database. This timezone will be applied to all datetime or Pandas Timestamp objects returned by the query.
* Parameter: column_tzs
  * Type: dict
  * Default: None
  * Description: A dictionary of column name to timezone name. Like query_tz, but allows specifying different timezones for different columns.
* Parameter: use_extended_dtypes
  * Type: bool
  * Default: True
  * Description: Use Pandas extended dtypes (like StringArray), and pandas.NA and pandas.NaT for ClickHouse NULL values. Applies only to query_df and query_df_stream methods.
* Parameter: external_data
  * Type: ExternalData
  * Default: None
  * Description: An ExternalData object containing file or binary data to use with the query. See Advanced Queries (External Data)
* Parameter: context
  * Type: QueryContext
  * Default: None
  * Description: A reusable QueryContext object can be used to encapsulate the above method arguments. See Advanced Queries (QueryContexts)


### Query examples[​](#query-examples "Direct link to Query examples")

#### Basic query[​](#basic-query "Direct link to Basic query")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Simple SELECT query
result = client.query("SELECT name, database FROM system.tables LIMIT 3")

# Access results as rows
for row in result.result_rows:
    print(row)
# Output:
# ('CHARACTER_SETS', 'INFORMATION_SCHEMA')
# ('COLLATIONS', 'INFORMATION_SCHEMA')
# ('COLUMNS', 'INFORMATION_SCHEMA')

# Access column names and types
print(result.column_names)
# Output: ("name", "database")
print([col_type.name for col_type in result.column_types])
# Output: ['String', 'String']

```


#### Accessing query results[​](#accessing-query-results "Direct link to Accessing query results")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

result = client.query("SELECT number, toString(number) AS str FROM system.numbers LIMIT 3")

# Row-oriented access (default)
print(result.result_rows)
# Output: [[0, "0"], [1, "1"], [2, "2"]]

# Column-oriented access
print(result.result_columns)
# Output: [[0, 1, 2], ["0", "1", "2"]]

# Named results (list of dictionaries)
for row_dict in result.named_results():
    print(row_dict)
# Output: 
# {"number": 0, "str": "0"}
# {"number": 1, "str": "1"}
# {"number": 2, "str": "2"}

# First row as dictionary
print(result.first_item)
# Output: {"number": 0, "str": "0"}

# First row as tuple
print(result.first_row)
# Output: (0, "0")

```


#### Query with client-side parameters[​](#query-with-client-side-parameters "Direct link to Query with client-side parameters")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Using dictionary parameters (printf-style)
query = "SELECT * FROM system.tables WHERE database = %(db)s AND name LIKE %(pattern)s"
parameters = {"db": "system", "pattern": "%query%"}
result = client.query(query, parameters=parameters)

# Using tuple parameters
query = "SELECT * FROM system.tables WHERE database = %s LIMIT %s"
parameters = ("system", 5)
result = client.query(query, parameters=parameters)

```


#### Query with server-side parameters[​](#query-with-server-side-parameters "Direct link to Query with server-side parameters")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Server-side binding (more secure, better performance for SELECT queries)
query = "SELECT * FROM system.tables WHERE database = {db:String} AND name = {tbl:String}"
parameters = {"db": "system", "tbl": "query_log"}

result = client.query(query, parameters=parameters)

```


#### Query with settings[​](#query-with-settings "Direct link to Query with settings")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Pass ClickHouse settings with the query
result = client.query(
    "SELECT sum(number) FROM numbers(1000000)",
    settings={
        "max_block_size": 100000,
        "max_execution_time": 30
    }
)

```


### The `QueryResult` object[​](#the-queryresult-object "Direct link to the-queryresult-object")

The base `query` method returns a `QueryResult` object with the following public properties:

*   `result_rows` -- A matrix of the data returned in the form of a Sequence of rows, with each row element being a sequence of column values.
*   `result_columns` -- A matrix of the data returned in the form of a Sequence of columns, with each column element being a sequence of the row values for that column
*   `column_names` -- A tuple of strings representing the column names in the `result_set`
*   `column_types` -- A tuple of ClickHouseType instances representing the ClickHouse data type for each column in the `result_columns`
*   `query_id` -- The ClickHouse query\_id (useful for examining the query in the `system.query_log` table)
*   `summary` -- Any data returned by the `X-ClickHouse-Summary` HTTP response header
*   `first_item` -- A convenience property for retrieving the first row of the response as a dictionary (keys are column names)
*   `first_row` -- A convenience property to return the first row of the result
*   `column_block_stream` -- A generator of query results in column oriented format. This property should not be referenced directly (see below).
*   `row_block_stream` -- A generator of query results in row oriented format. This property should not be referenced directly (see below).
*   `rows_stream` -- A generator of query results that yields a single row per invocation. This property should not be referenced directly (see below).
*   `summary` -- As described under the `command` method, a dictionary of summary information returned by ClickHouse

The `*_stream` properties return a Python Context that can be used as an iterator for the returned data. They should only be accessed indirectly using the Client `*_stream` methods.

The complete details of streaming query results (using StreamContext objects) are outlined in [Advanced Queries (Streaming Queries)](about:/docs/integrations/language-clients/python/advanced-querying#streaming-queries).

Consuming query results with NumPy, Pandas or Arrow[​](#consuming-query-results-with-numpy-pandas-or-arrow "Direct link to Consuming query results with NumPy, Pandas or Arrow")
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

ClickHouse Connect provides specialized query methods for NumPy, Pandas, and Arrow data formats. For detailed information on using these methods, including examples, streaming capabilities, and advanced type handling, see [Advanced Querying (NumPy, Pandas and Arrow Queries)](about:/docs/integrations/language-clients/python/advanced-querying#numpy-pandas-and-arrow-queries).

Client streaming query methods[​](#client-streaming-query-methods "Direct link to Client streaming query methods")
------------------------------------------------------------------------------------------------------------------

For streaming large result sets, ClickHouse Connect provides multiple streaming methods. See [Advanced Queries (Streaming Queries)](about:/docs/integrations/language-clients/python/advanced-querying#streaming-queries) for details and examples.

Client `insert` Method[​](#client-insert-method "Direct link to client-insert-method")
--------------------------------------------------------------------------------------

For the common use case of inserting multiple records into ClickHouse, there is the `Client.insert` method. It takes the following parameters:



* Parameter: table
  * Type: str
  * Default: Required
  * Description: The ClickHouse table to insert into. The full table name (including database) is permitted.
* Parameter: data
  * Type: Sequence of Sequences
  * Default: Required
  * Description: The matrix of data to insert, either a Sequence of rows, each of which is a sequence of column values, or a Sequence of columns, each of which is a sequence of row values.
* Parameter: column_names
  * Type: Sequence of str, or str
  * Default: '*'
  * Description: A list of column_names for the data matrix. If '*' is used instead, ClickHouse Connect will execute a "pre-query" to retrieve all of the column names for the table.
* Parameter: database
  * Type: str
  * Default: ''
  * Description: The target database of the insert. If not specified, the database for the client will be assumed.
* Parameter: column_types
  * Type: Sequence of ClickHouseType
  * Default: None
  * Description: A list of ClickHouseType instances. If neither column_types or column_type_names is specified, ClickHouse Connect will execute a "pre-query" to retrieve all the column types for the table.
* Parameter: column_type_names
  * Type: Sequence of ClickHouse type names
  * Default: None
  * Description: A list of ClickHouse datatype names. If neither column_types or column_type_names is specified, ClickHouse Connect will execute a "pre-query" to retrieve all the column types for the table.
* Parameter: column_oriented
  * Type: bool
  * Default: False
  * Description: If True, the data argument is assumed to be a Sequence of columns (and no "pivot" will be necessary to insert the data). Otherwise data is interpreted as a Sequence of rows.
* Parameter: settings
  * Type: dict
  * Default: None
  * Description: See settings description.
* Parameter: context
  * Type: InsertContext
  * Default: None
  * Description: A reusable InsertContext object can be used to encapsulate the above method arguments. See Advanced Inserts (InsertContexts)
* Parameter: transport_settings
  * Type: dict
  * Default: None
  * Description: Optional dictionary of transport-level settings (HTTP headers, etc.)


This method returns a "query summary" dictionary as described under the "command" method. An exception will be raised if the insert fails for any reason.

For specialized insert methods that work with Pandas DataFrames, PyArrow Tables, and Arrow-backed DataFrames, see [Advanced Inserting (Specialized Insert Methods)](about:/docs/integrations/language-clients/python/advanced-inserting#specialized-insert-methods).

Note

A NumPy array is a valid Sequence of Sequences and can be used as the `data` argument to the main `insert` method, so a specialized method is not required.

### Examples[​](#examples "Direct link to Examples")

The examples below assume an existing table `users` with schema `(id UInt32, name String, age UInt8)`.

#### Basic row-oriented insert[​](#basic-row-oriented-insert "Direct link to Basic row-oriented insert")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Row-oriented data: each inner list is a row
data = [
    [1, "Alice", 25],
    [2, "Bob", 30],
    [3, "Joe", 28],
]

client.insert("users", data, column_names=["id", "name", "age"])

```


#### Column-oriented insert[​](#column-oriented-insert "Direct link to Column-oriented insert")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Column-oriented data: each inner list is a column
data = [
    [1, 2, 3],  # id column
    ["Alice", "Bob", "Joe"],  # name column
    [25, 30, 28],  # age column
]

client.insert("users", data, column_names=["id", "name", "age"], column_oriented=True)

```


#### Insert with explicit column types[​](#insert-with-explicit-column-types "Direct link to Insert with explicit column types")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

# Useful when you want to avoid a DESCRIBE query to the server
data = [
    [1, "Alice", 25],
    [2, "Bob", 30],
    [3, "Joe", 28],
]

client.insert(
    "users",
    data,
    column_names=["id", "name", "age"],
    column_type_names=["UInt32", "String", "UInt8"],
)

```


#### Insert into specific database[​](#insert-into-specific-database "Direct link to Insert into specific database")

```
import clickhouse_connect

client = clickhouse_connect.get_client()

data = [
    [1, "Alice", 25],
    [2, "Bob", 30],
]

# Insert into a table in a specific database
client.insert(
    "users",
    data,
    column_names=["id", "name", "age"],
    database="production",
)

```


File Inserts[​](#file-inserts "Direct link to File Inserts")
------------------------------------------------------------

For inserting data directly from files into ClickHouse tables, see [Advanced Inserting (File Inserts)](about:/docs/integrations/language-clients/python/advanced-inserting#file-inserts).

Raw API[​](#raw-api "Direct link to Raw API")
---------------------------------------------

For advanced use cases requiring direct access to ClickHouse HTTP interfaces without type transformations, see [Advanced Usage (Raw API)](about:/docs/integrations/language-clients/python/advanced-usage#raw-api).

Utility classes and functions[​](#utility-classes-and-functions "Direct link to Utility classes and functions")
---------------------------------------------------------------------------------------------------------------

The following classes and functions are also considered part of the "public" `clickhouse-connect` API and are, like the classes and methods documented above, stable across minor releases. Breaking changes to these classes and functions will only occur with a minor (not patch) release and will be available with a deprecated status for at least one minor release.

### Exceptions[​](#exceptions "Direct link to Exceptions")

All custom exceptions (including those defined in the DB API 2.0 specification) are defined in the `clickhouse_connect.driver.exceptions` module. Exceptions actually detected by the driver will use one of these types.

### ClickHouse SQL utilities[​](#clickhouse-sql-utilities "Direct link to ClickHouse SQL utilities")

The functions and the DT64Param class in the `clickhouse_connect.driver.binding` module can be used to properly build and escape ClickHouse SQL queries. Similarly, the functions in the `clickhouse_connect.driver.parser` module can be used to parse ClickHouse datatype names.

Multithreaded, multiprocess, and async/event driven use cases[​](#multithreaded-multiprocess-and-asyncevent-driven-use-cases "Direct link to Multithreaded, multiprocess, and async/event driven use cases")
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

For information on using ClickHouse Connect in multithreaded, multiprocess, and async/event-driven applications, see [Advanced Usage (Multithreaded, multiprocess, and async/event driven use cases)](about:/docs/integrations/language-clients/python/advanced-usage#multithreaded-multiprocess-and-asyncevent-driven-use-cases).

AsyncClient wrapper[​](#asyncclient-wrapper "Direct link to AsyncClient wrapper")
---------------------------------------------------------------------------------

For information on using the AsyncClient wrapper for asyncio environments, see [Advanced Usage (AsyncClient wrapper)](about:/docs/integrations/language-clients/python/advanced-usage#asyncclient-wrapper).

Managing ClickHouse Session IDs[​](#managing-clickhouse-session-ids "Direct link to Managing ClickHouse Session IDs")
---------------------------------------------------------------------------------------------------------------------

For information on managing ClickHouse session IDs in multi-threaded or concurrent applications, see [Advanced Usage (Managing ClickHouse Session IDs)](about:/docs/integrations/language-clients/python/advanced-usage#managing-clickhouse-session-ids).

Customizing the HTTP connection pool[​](#customizing-the-http-connection-pool "Direct link to Customizing the HTTP connection pool")
------------------------------------------------------------------------------------------------------------------------------------

For information on customizing the HTTP connection pool for large multi-threaded applications, see [Advanced Usage (Customizing the HTTP connection pool)](about:/docs/integrations/language-clients/python/advanced-usage#customizing-the-http-connection-pool).