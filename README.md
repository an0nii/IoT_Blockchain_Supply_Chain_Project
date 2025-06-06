# IoT Blockchain Supply Chain Project

Этот проект представляет собой веб-платформу для управления цепочками поставок с использованием современных технологий фронтенда, бэкенда и блокчейна. Приложение позволяет:
- Добавлять IoT-устройства с регистрацией в блокчейне через MetaMask и смарт-контракт.
- Просматривать список устройств и их подробные данные.
- Получать информацию о товарах, связанных с устройствами.
- Генерировать метки и QR-коды для товаров.
- Подключать кошелек через библиотеку vue-connect-wallet на фронтенде.

## Установка и запуск

### Бэкенд

1. Перейдите в директорию `backend`:
   ```bash
   cd .../IoT_Blockchain_CW/backend
   ```
2. Создайте и активируйте виртуальное окружение (рекомендуется):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirments.txt
   ```
4. Запустите сервер:
   ```bash
   python server.py
   ```
   Сервер будет доступен по адресу `http://localhost:3000`.

### Фронтенд

1. Перейдите в директорию `frontend`:
   ```bash
   cd .../IoT_Blockchain_CW/frontend
   ```
2. Установите npm-зависимости:
   ```bash
   npm install
   ```
3. Запустите проект в режиме разработки:
   ```bash
   npm run serve
   ```
   Приложение будет запущено, и вы сможете открыть его в браузере по адресу, указанному в терминале (обычно `http://localhost:8080`).

## Используемые технологии

- **Фронтенд:**
  - Vue.js и Vue Router для создания одностраничных приложений.
  - Tailwind CSS для быстрой стилизации и создания адаптивного интерфейса.
  - vue-connect-wallet для интеграции MetaMask в интерфейс.
  - ethers.js для взаимодействия с Ethereum-сетью и смарт-контрактами.

- **Бэкенд:**
  - Flask с flask-cors для создания RESTful API.
  - pyqrcode, pypng, zlib, base64 для генерации и обработки QR-кодов.

- **Блокчейн:**
  - Смарт-контракт (IOTContractMonitoring) для авторизации устройств и управления метками.

## Будущие планы

- **Перенос управления состоянием:** Рассмотреть использование Pinia для централизованного управления состоянием приложения вместо localStorage/sessionStorage.
- **Улучшение интерфейса:** Доработка дизайна и повышение удобства использования.
- **Оптимизация бэкенда:** Обработка ошибок, повышение производительности, а также масштабирование серверной части.
- **Интеграция с серверными базами данных:** Переход на более надежное хранилище данных для совместного доступа пользователей и лучшей безопасности.