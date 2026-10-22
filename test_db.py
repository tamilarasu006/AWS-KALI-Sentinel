import asyncio
from dotenv import load_dotenv
load_dotenv(".env", override=True)

from OpenDEMON.database.engine import _build_engine
from OpenDEMON.database.repositories.users import UserRepository
from OpenDEMON.server.auth_routes import local_user_store
from sqlalchemy.ext.asyncio import async_sessionmaker

async def sync():
    eng = _build_engine()
    factory = async_sessionmaker(bind=eng, autocommit=False, autoflush=False)
    async with factory() as session:
        repo = UserRepository(session)
        for email, u in local_user_store._users.items():
            db_u = await repo.get_by_email(email)
            if not db_u:
                name = u.get("name", "Operative")
                print(f"Syncing {email} ({name}) to Supabase...")
                await repo.create_user(email=email, name=name)
            else:
                print(f"{email} already exists in Supabase.")
    await eng.dispose()
    print("Sync complete!")

asyncio.run(sync())
