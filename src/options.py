
from common.options import define

# Main

define("host",
       default="http://localhost:9517",
       help="Public hostname of this service",
       type=str)

define("listen",
       default="port:9517",
       help="Socket to listen. Could be a port number (port:N), or a unix domain socket (unix:PATH)",
       type=str)

define("name",
       default="report",
       help="Service short name. User to discover by discovery service.",
       type=str)

# MySQL database

define("db_host",
       default="127.0.0.1",
       type=str,
       help="MySQL database location")

define("db_username",
       default="root",
       type=str,
       help="MySQL account username")

define("db_password",
       default="",
       type=str,
       help="MySQL account password")

define("db_name",
       default="dev_report",
       type=str,
       help="MySQL database name")

# Rate limit cache

define("rate_cache_host",
       default="127.0.0.1",
       help="Location of a ratelimit cache (redis).",
       group="ratelimit",
       type=str)

define("rate_cache_port",
       default=6379,
       help="Port of ratelimit cache (redis).",
       group="ratelimit",
       type=int)

define("rate_cache_db",
       default=7,
       help="Database of ratelimit cache (redis).",
       group="ratelimit",
       type=int)

define("rate_cache_max_connections",
       default=500,
       help="Maximum connections to the ratelimit cache (connection pool).",
       group="ratelimit",
       type=int)

define("rate_report_upload",
       default="10,600",
       help="A limit for report upload for user tuple: (amount, time)",
       group="ratelimit",
       type=str)

# Regular cache

define("cache_host",
       default="localhost",
       help="Location of a regular cache (redis).",
       group="cache",
       type=str)

define("cache_port",
       default=6379,
       help="Port of regular cache (redis).",
       group="cache",
       type=int)

define("cache_db",
       default=4,
       help="Database of regular cache (redis).",
       group="cache",
       type=int)

define("cache_max_connections",
       default=500,
       help="Maximum connections to the regular cache (connection pool).",
       group="cache",
       type=int)

# Static

define("max_report_size",
       default=1048576,
       help="Maximum report size to accept",
       group="static",
       type=str)
