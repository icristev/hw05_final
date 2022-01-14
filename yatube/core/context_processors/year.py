import datetime as dt


def year(request):
    """Создаём переменную, которая будет показывать текущий год."""
    return {
        'year': int(dt.date.today().strftime('%Y'))
    }
