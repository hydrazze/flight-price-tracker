from aiogram import Router

from app.handlers.start import router as start_router
from app.handlers.track import router as track_router
from app.handlers.my_tracks import router as my_tracks_router


router = Router()

router.include_router(start_router)
router.include_router(track_router)
router.include_router(my_tracks_router)