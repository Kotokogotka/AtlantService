"""
Раздача собранного React-приложения (для запуска бэка и фронта одной командой).
"""
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
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


class ServeBuildStaticView(View):
    """Отдаёт файлы из front_football/build/static/ по URL /static/."""

    def get(self, request, path):
        build_static = settings.FRONTEND_BUILD_DIR / 'static'
        if not build_static.is_dir():
            raise Http404
        # Защита от path traversal
        full_path = (build_static / path).resolve()
        try:
            full_path.relative_to(build_static.resolve())
        except ValueError:
            raise Http404
        if not full_path.is_file():
            raise Http404
        return FileResponse(open(full_path, 'rb'))
