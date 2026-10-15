import asyncio
import asyncpg
import ssl

async def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    conn = await asyncpg.connect('postgresql://postgres.ukktdaqtiujypfhigwld:Tjbcisahgcu%2A%26%25%25HVJgc43Hvhgf%26%258KJB68KJVUy9%2A%29KJBkh%5E%2A@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres', ssl=ctx)
    
    records = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'agent_runs'")
    for r in records:
        print(f"{r['column_name']} : {r['data_type']}")
    await conn.close()

asyncio.run(main())
