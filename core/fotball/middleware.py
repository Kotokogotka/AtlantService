"""
Middleware для обработки проблем с кодировкой
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from .utils import safe_decode, normalize_text

logger = logging.getLogger(__name__)


class EncodingFixMiddleware(MiddlewareMixin):
    """
    Middleware для исправления проблем с кодировкой в запросах и ответах
    """
    
    def process_request(self, request):
        """
        Обработка входящего запроса
        """
        # Исправляем кодировку в POST данных
        if request.method == 'POST' and hasattr(request, '_body'):
            try:
                if isinstance(request._body, bytes):
                    # Пытаемся безопасно декодировать тело запроса
                    decoded_body = safe_decode(request._body)
                    request._body = decoded_body.encode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to fix encoding in request body: {e}")
        
        # Исправляем кодировку в заголовках
        if hasattr(request, 'META'):
            for key, value in request.META.items():
                if isinstance(value, str):
                    try:
                        request.META[key] = normalize_text(value)
                    except Exception as e:
                        logger.warning(f"Failed to normalize META field {key}: {e}")
        
        return None
    
    def process_response(self, request, response):
        """
        Обработка исходящего ответа
        """
        # Убеждаемся, что ответ имеет правильную кодировку
        if isinstance(response, HttpResponse):
            if hasattr(response, 'content') and response.content:
                try:
                    # Проверяем, что контент можно декодировать как UTF-8
                    if isinstance(response.content, bytes):
                        content_str = safe_decode(response.content)
                        response.content = content_str.encode('utf-8')
                    
                    # Устанавливаем правильный заголовок Content-Type
                    if 'Content-Type' not in response:
                        response['Content-Type'] = 'application/json; charset=utf-8'
                    elif 'charset' not in response['Content-Type']:
                        response['Content-Type'] += '; charset=utf-8'
                        
                except Exception as e:
                    logger.warning(f"Failed to fix encoding in response: {e}")
        
        return response


class UnicodeErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware для глобальной обработки ошибок Unicode
    """
    
    def process_exception(self, request, exception):
        """
        Обработка исключений, связанных с кодировкой
        """
        if isinstance(exception, UnicodeDecodeError):
            logger.error(f"Unicode decode error: {exception}")
            
            # Попытка восстановления
            try:
                error_details = {
                    'error': 'Ошибка кодировки',
                    'message': 'Проблема с кодировкой данных. Попробуйте использовать UTF-8.',
                    'details': str(exception),
                    'position': getattr(exception, 'start', None),
                    'problematic_byte': hex(exception.object[exception.start]) if hasattr(exception, 'start') else None
                }
                
                response_content = {
                    'error': True,
                    'message': 'Ошибка обработки данных. Проверьте кодировку.',
                    'details': error_details
                }
                
                import json
                response = HttpResponse(
                    json.dumps(response_content, ensure_ascii=False),
                    content_type='application/json; charset=utf-8',
                    status=400
                )
                return response
                
            except Exception as e:
                logger.error(f"Failed to handle Unicode error: {e}")
        
        elif isinstance(exception, UnicodeEncodeError):
            logger.error(f"Unicode encode error: {exception}")
            
            response_content = {
                'error': True,
                'message': 'Ошибка кодирования данных.',
                'details': str(exception)
            }
            
            import json
            response = HttpResponse(
                json.dumps(response_content, ensure_ascii=False),
                content_type='application/json; charset=utf-8',
                status=500
            )
            return response
        
        return None