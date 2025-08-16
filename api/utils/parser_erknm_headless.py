from playwright.sync_api import sync_playwright, TimeoutError
from typing import Dict
import logging
import sys
from .logging_config import logger


class ParserError(Exception):
    """Пользовательское исключение для ошибок парсера"""
    pass

# Функция для безопасного извлечения текста


def safe_extract(page, selector) -> str:
    try:
        content = page.locator(selector).first.text_content(
            timeout=3000).strip()
        logger.debug(f'{safe_extract.__name__}: Данные КНМ распознаны.')
        return content

    except Exception:
        logger.debug(f'{safe_extract.__name__}: Отсутствуют данные КНМ.')
        return 'Не найдено'


def parse_knm_data(url: str) -> Dict[str, str]:
    with sync_playwright() as p:
        verifiable_data = {
            'Номер КНМ': (
                'div._Row_1bklp_108:has('
                'div._ColText_1bklp_124:has-text("Учетный номер КНМ в соответствии")) '
                'div._ColValue_1bklp_130'
            ),
            'Статус КНМ': (
                'div._Row_1bklp_108:has('
                'div._ColText_1bklp_124:has-text("Статус КНМ")) '
                'div._ColValue_1bklp_130'
            ),
            'Дата регистрации': (
                'div._Row_1bklp_108:has('
                'div._ColText_1bklp_124:has-text('
                '"Дата регистрации в ФГИС ЕРКНМ")) '
                'div._ColValue_1bklp_130'
            ),
            'Дата начала': (
                'div._Row_1bklp_108:has('
                'div._ColText_1bklp_124:has-text("Дата начала КНМ")) '
                'div._ColValue_1bklp_130'),
            'Дата окончания': (
                'div._Row_1bklp_108:has('
                'div._ColText_1bklp_124:has-text("Дата окончания КНМ")) '
                'div._ColValue_1bklp_130'),
            'Адрес': (
                'div._Row_1bklp_108:has('
                'div._ColText_1bklp_124:has-text("Адрес")) '
                'div._ColValue_1bklp_130')
        }

        # Настройка headless-браузера
        browser = p.chromium.launch(
            headless=True,  # Работает в фоне
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",  # Для стабильности в Docker/CI
                "--no-sandbox"
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 1024}
        )
        page = context.new_page()

        # Обход защиты
        page.add_init_script("""
            delete Object.getPrototypeOf(navigator).webdriver;
            window.navigator.chrome = { runtime: {} };
        """)
        logger.debug(
            f'{parse_knm_data.__name__}: Браузер настроен: {browser.browser_type.name}.')
        try:
            logger.debug(
                f'{parse_knm_data.__name__}: Загружаем страницу: {url}.')
            # Загрузка страницы с улучшенным ожиданием
            page.goto(url, wait_until="networkidle", timeout=30000)
            logger.debug(
                f'{parse_knm_data.__name__}: '
                'Cтраница загружена, определяем ключевые элементы.'
            )
            # Явное ожидание ключевых элементов
            page.locator('div._Row_1bklp_108')
            content_value = {stat: safe_extract(
                page, val) for stat, val in verifiable_data.items()}
            logger.debug(
                f'{parse_knm_data.__name__}: '
                f'Определены ключевые элементы: {", ".join(content_value)}.'
            )
            return content_value

        except TimeoutError:
            logger.warning(
                f'{parse_knm_data.__name__}: '
                'Превышено время ожидания загрузки страниц.'
            )
            raise ParserError('Превышено время ожидания загрузки страниц.')
        except Exception as e:
            logger.warning(
                f'{parse_knm_data.__name__}: '
                f'Критическая ошибка: {str(e)}.'
            )
            raise ParserError(f'Критическая ошибка: {str(e)}.')
        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()


# Пример вызова
if __name__ == "__main__":
    url_yes = "https://proverki.gov.ru/portal/public-knm/link-only/77c98f91-f64b-4aac-a260-7bdc3a915b29"

    result = parse_knm_data(url_yes)

    print("Результаты:")
    for key, value in result.items():
        print(f"{key}: {value}")
