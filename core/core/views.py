"""
Раздача собранного React-приложения (для запуска бэка и фронта одной командой).
"""
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views import View


class ServeReactAppView(View):
    """Отдаёт index.html билда фронта (SPA: все пути ведут на один HTML)."""

    def get(self, request, *args, **kwargs):
        index_path = settings.FRONTEND_BUILD_DIR / 'index.html'
        if not index_path.is_file():
            return HttpResponse(
                'Фронт не собран. Выполните: cd front_football && npm run build',
                status=503,
                content_type='text/plain; charset=utf-8',
            )
        return FileResponse(
            open(index_path, 'rb'),
            content_type='text/html',
        )
