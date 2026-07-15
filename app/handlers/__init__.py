from aiogram import Router

from app.handlers.start import router as start_router
from app.handlers.track import router as track_router


router = Router()

router.include_router(start_router)
router.include_router(track_router)