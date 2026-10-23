from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Enum,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.enums import StopPreference, TrackStatus

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.user import User



class Track(Base):

    __tablename__ = "tracks"
    __table_args__ = (
        CheckConstraint(
            "return_date IS NULL OR return_date >= departure_date",
            name="ck_tracks_return_date",
        ),
    )


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


    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    stop_preference: Mapped[StopPreference] = mapped_column(
        Enum(
            StopPreference, name="stoppreference", native_enum=False,
            create_constraint=True,
        ),
        default=StopPreference.ANY,
        server_default="ANY",
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


    # Snapshot of the cheapest matching offer; always corresponds to last_price.
    last_offer: Mapped[dict | None] = mapped_column(JSON, nullable=True)

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
