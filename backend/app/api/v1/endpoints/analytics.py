from fastapi import APIRouter
from fastapi.responses import Response
from app.services.analytics_service import analytics_service
from app.schemas.analytics_schema import AnalyticsSummary

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary():
    return await analytics_service.get_analytics_summary()


@router.get("/export/csv")
async def export_csv_report():
    csv_data = await analytics_service.generate_csv_report()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metroflow_performance_report.csv"}
    )
