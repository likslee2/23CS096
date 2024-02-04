from sqlalchemy import create_engine
import os

db_connection_str = os.environ["DB_CONNECTION_STR"]

engine = create_engine(db_connection_str, connect_args={
                                "ssl": {
                                    "ssl_ca": "/etc/ssl/cert.pem"
                                }
                            }
                        )