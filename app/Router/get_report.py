from fastapi import APIRouter, Response
from app.report import get_report_status_from_db, get_report_data_from_db


router = APIRouter()

@router.get('/get_report')
def get_report(report_id: str):
    try:
        if not report_id:
            return {'error': 'Missing report ID', 'error_code': 400}

        report_status = get_report_status_from_db(report_id)
        if not report_status:
            return {'error': 'Invalid report ID', 'error_code': 400}

        if report_status == 'Running':
            return {'status': 'Running', 'message': 'Success', 'error_code': 200}
        elif report_status == 'Complete':
            report_data = get_report_data_from_db(report_id)
            if report_data:
                return Response(report_data, media_type='text/csv')
            else:
                return {'error': 'Failed to retrieve report data', 'error_code': 400}
        else:
            return {'error': 'Invalid report status', 'error_code': 400}
    except Exception as e:
        return {'error_message': 'Something went wrong', 'error_code': 500, 'error': str(e)}