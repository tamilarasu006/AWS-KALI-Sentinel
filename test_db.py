import asyncio
import asyncpg
import ssl

async def main():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        conn = await asyncpg.connect(
            "postgresql://postgres.ukktdaqtiujypfhigwld:Tjbcisahgcu%2A%26%25%25HVJgc43Hvhgf%26%258KJB68KJVUy9%2A%29KJBkh%5E%2A@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres",
            ssl=ctx
        )
        print("Success! Connected.")
        await conn.execute('SELECT 1')
        await conn.close()
    except Exception as e:
        print(f"Error: {type(e).__name__} - {e}")

asyncio.run(main())
