from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://h734vx8ogcefr59w3rrn:pscale_pw_BDCZJgTGVyMiPbcjXUeYVRZoU2Q8TStpMEGzd0jKaDL@aws.connect.psdb.cloud/pcparts?charset=utf8mb4",
                            connect_args={
                                "ssl": {
                                    "ssl_ca": "/etc/ssl/cert.pem"
                                }
                            }
                        )

