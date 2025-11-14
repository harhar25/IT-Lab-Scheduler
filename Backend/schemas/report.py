from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class ReportBase(BaseModel):
    start_date: datetime
    end_date: datetime
    report_type: str

class UsageStats(BaseModel):
    lab_name: str
    total_hours: int
    utilization_rate: float
    peak_day: str
    peak_hours: str

class PeakHourData(BaseModel):
    time_slot: str
    utilization: float

class MonthlyReport(BaseModel):
    period: str
    data: List[UsageStats]
    peak_hours: List[PeakHourData]

class InstructorUsage(BaseModel):
    instructor_name: str
    total_reservations: int
    total_hours: int
    favorite_lab: str

class InstructorReport(BaseModel):
    period: str
    data: List[InstructorUsage]