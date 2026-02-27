import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Integer, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Category(enum.Enum):
    OFFICE = "office"
    PERSONAL = "personal"
    CHORES = "chores"
    FITNESS = "fitness"

task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True),
    Column("depends_on_id", UUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True),
)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    category = Column(Enum(Category), default=Category.PERSONAL)
    priority = Column(Integer, default=1)  # 1: Low, 2: Medium, 3: High
    
    # Roadmap association
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id"), nullable=True)
    roadmap = relationship("Roadmap", back_populates="tasks")

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.task_id,
        secondaryjoin=id == task_dependencies.c.depends_on_id,
        backref="dependent_tasks",
        lazy="joined",
    )

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal = Column(Text, nullable=False)
    tasks = relationship("Task", back_populates="roadmap", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=datetime.utcnow)