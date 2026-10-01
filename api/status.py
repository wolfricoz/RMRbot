from fastapi import APIRouter

from databases.transactions.DatabaseTransactions import DatabaseTransactions
from classes.queue import queue

router = APIRouter()


@router.post("/ping")
async def ping():
    status = DatabaseTransactions.ping_db()
    q = queue()
    return {
        "status"               : status,
        "high_priority_queue"  : len(q.high_priority_queue),
        "normal_priority_queue": len(q.normal_priority_queue),
        "low_priority_queue"   : len(q.low_priority_queue),
    }
