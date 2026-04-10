import logging
import os
import urllib.parse

from azure.identity import AzureDeveloperCliCredential
from pgvector.asyncpg import register_vector
from sqlalchemy import event
from sqlalchemy.engine import AdaptedConnection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from fastapi_app.dependencies import get_azure_credential

logger = logging.getLogger("ragapp")


async def create_postgres_engine(
    *, host, username, database, password, sslmode, azure_credential
) -> AsyncEngine:

    def get_password_from_azure_credential():
        token = azure_credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        )
        return token.token

    # ✅ Read flag from env
    use_azure_identity = os.environ.get("USE_AZURE_IDENTITY", "false").lower() == "true"

    token_based_password = False

    if host.endswith(".database.azure.com") and use_azure_identity:
        token_based_password = True
        logger.info("Authenticating using Azure Identity...")

        if azure_credential is None:
            raise ValueError("Azure credential required for Azure Identity")

        password = get_password_from_azure_credential()

    else:
        logger.info("Authenticating using username/password...")

    # ✅ IMPORTANT: encode username & password safely
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password) if password else ""

    DATABASE_URI = f"postgresql+asyncpg://{encoded_username}:{encoded_password}@{host}/{database}"

    # ✅ Correct SSL handling for asyncpg
    connect_args = {}
    if sslmode and sslmode.lower() == "require":
        connect_args["ssl"] = "require"

    # 🔍 Debug (remove later)
    print("DB URI:", DATABASE_URI)

    engine = create_async_engine(
        DATABASE_URI,
        echo=False,
        connect_args=connect_args,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def register_custom_types(dbapi_connection: AdaptedConnection, *args):
        logger.info("Registering pgvector extension...")
        try:
            dbapi_connection.run_async(register_vector)
        except ValueError:
            logger.warning("pgvector extension not created yet")

    @event.listens_for(engine.sync_engine, "do_connect")
    def update_password_token(dialect, conn_rec, cargs, cparams):
        if token_based_password:
            logger.info("Refreshing Azure token...")
            cparams["password"] = get_password_from_azure_credential()

    return engine


async def create_postgres_engine_from_env(azure_credential=None) -> AsyncEngine:

    use_azure_identity = os.environ.get("USE_AZURE_IDENTITY", "false").lower() == "true"

    if use_azure_identity and azure_credential is None:
        azure_credential = get_azure_credential()

    return await create_postgres_engine(
        host=os.environ["POSTGRES_HOST"],
        username=os.environ["POSTGRES_USERNAME"],
        database=os.environ["POSTGRES_DATABASE"],
        password=os.environ.get("POSTGRES_PASSWORD"),
        sslmode=os.environ.get("POSTGRES_SSLMODE"),
        azure_credential=azure_credential,
    )


async def create_postgres_engine_from_args(args, azure_credential=None) -> AsyncEngine:

    use_azure_identity = os.environ.get("USE_AZURE_IDENTITY", "false").lower() == "true"

    if use_azure_identity and azure_credential is None:
        if args.tenant_id:
            logger.info(
                "Authenticating using Azure CLI Credential for tenant %s",
                args.tenant_id,
            )
            azure_credential = AzureDeveloperCliCredential(
                tenant_id=args.tenant_id, process_timeout=60
            )
        else:
            logger.info("Authenticating using Azure CLI Credential")
            azure_credential = AzureDeveloperCliCredential(process_timeout=60)

    return await create_postgres_engine(
        host=args.host,
        username=args.username,
        database=args.database,
        password=args.password,
        sslmode=args.sslmode,
        azure_credential=azure_credential,
    )