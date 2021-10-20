from datetime import datetime


def year(request):
    current_date = datetime.now()
    year = current_date.year
    """Добавляет переменную с текущим годом."""
    return {
        'year': year
    }
