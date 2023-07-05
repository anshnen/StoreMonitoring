import secrets
from fastapi import APIRouter
from app.report import generate_report

router = APIRouter()

@router.get('/trigger_report')
def trigger_report():
    try:
        report_id = secrets.token_urlsafe(16)
        generate_report(report_id)
        return {'report_id': report_id, 'message': 'Success', 'error_code': 200}
    except Exception as e:
        return {'error_message': 'Something went wrong', 'error_code': 500, 'error': str(e)}