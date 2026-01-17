# QuantCore Platform
### Physics-Informed Algorithmic Trading System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![C#](https://img.shields.io/badge/C%23-.NET%209.0-purple?logo=dotnet&logoColor=white)](https://dotnet.microsoft.com/)
[![Docker](https://img.shields.io/badge/Docker-Microservices-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-TimeSeries-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **QuantCore** — это исследовательская торговая платформа, объединяющая методы **Эконофизики** (Square-Root Law of Market Impact) и **Глубокого обучения** (Physics-Informed Neural Networks) для поиска рыночных неэффективностей в реальном времени.

---

## Интерфейс Терминала (The Boss)

Профессиональный десктопный терминал (WPF / .NET 9), визуализирующий рыночную микроструктуру.

![Terminal Screenshot](assets/terminal_screenshot.png)
*(Сверху: Рыночные данные. Снизу: Индикатор Z-Score, показывающий "сжатие пружины" ликвидности)*

---

## Архитектура Системы

Проект построен на базе микросервисной архитектуры (Event-Driven), обеспечивающей надежность и масштабируемость.

| Сервис | Технологии | Роль в системе |
| :--- | :--- | :--- |
| **The Brain** | Python, FastAPI, PyTorch | **R&D Ядро.** Рассчитывает физические модели, обучает нейросети (PINN), предоставляет API для прогнозов. |
| **The Muscle** | Python (AsyncIO), gRPC | **Data Ingestion.** Держит постоянное соединение с биржей, стримит тики и свечи в базу данных без потерь. |
| **The Boss** | C# (WPF), ScottPlot | **User Interface.** Визуализация данных, управление сигналами, профессиональные графики. |
| **Storage** | PostgreSQL, Redis | **Persistence.** Хранение исторических данных и быстрый кэш. |

---

## Научная База (The Science)

В основе стратегии лежит **Закон Квадратного Корня** (Square-Root Law of Price Impact), доказанный на данных MOEX.

$$ I \approx Y \cdot \sigma \cdot \left( \frac{Q}{V} \right)^\delta $$

Где $\delta \approx 0.44$ (эмпирическая константа для рынка РФ).

### Алгоритм поиска Аномалий
1.  **Калибровка:** Система рассчитывает "идеальное" влияние объема на цену для каждого актива.
2.  **Z-Score:** Мы измеряем отклонение реальной цены от теоретической модели.
    *   **Z < -2.0:** (Сигнал Buy) Огромный объем не сдвинул цену $\rightarrow$ Лимитная плотность ("Айсберг") $\rightarrow$ Накопление энергии.
3.  **PINN Validation:** Нейросеть (LSTM), обученная с учетом физических ограничений (Physics Loss), подтверждает или отвергает сигнал.

---

## Установка и Запуск

### Предварительные требования
*   Docker Desktop
*   .NET 9.0 SDK
*   Токен T-Bank API (в файле `.env`)

### 1. Запуск Инфраструктуры (Бэкенд)
Поднимаем базу данных, API и стример данных одной командой:

```bash
docker-compose up --build -d
```
Brain API будет доступен по адресу: http://localhost:8000/docs
Muscle начнет автоматический сбор данных в PostgreSQL.

### 2. Запуск Терминала (Фронтенд)
Откройте терминал в папке UI и запустите клиент:
```Bash
cd services/dotnet-boss
dotnet run --project QuantCore.UI
```
## Результаты исследований
На исторических данных (Backtest) стратегия поиска аномалий Z-Score показала высокую эффективность на активах средней ликвидности (Mid-Caps).
**SBER (High Liquidity):**  Рынок эффективен ($$   R^2 \approx 0.99   $$), аномалий мало.

**SELG/FLOT (Mid Liquidity):** Найдены устойчивые паттерны "сжатия пружины" с последующим импульсом цены.

## Tech Stack Details
**Backend:** Python 3.11, FastAPI, SQLAlchemy, AsyncPG.
**ML / Math:** PyTorch (LSTM + Physics Loss), SciPy, NumPy, Pandas.
**Frontend:** C# .NET 9, WPF, MVVM, ScottPlot 5, Entity Framework Core.
**DevOps:** Docker Compose.

## Disclaimer
Программное обеспечение предоставляется "как есть". Автор не несет ответственности за финансовые риски. Используйте на свой страх и риск.

**Developed with love for Science & Profit.**