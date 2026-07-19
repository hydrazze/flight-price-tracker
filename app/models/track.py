from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.enums import TrackStatus

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.user import User



class Track(Base):

    __tablename__ = "tracks"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )


    user: Mapped["User"] = relationship(
        back_populates="tracks"
    )


    # Код аэропорта отправления
    # Например: MOW
    origin: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )


    # Код аэропорта назначения
    # Например: KZN
    destination: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )


    departure_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )


    target_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


    last_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


    status: Mapped[TrackStatus] = mapped_column(
        Enum(
            TrackStatus,
            name="trackstatus",
        ),
        default=TrackStatus.UNKNOWN,
        nullable=False,
    )


    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


    no_flights_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )