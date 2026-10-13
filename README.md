# iis-project-<medvid>

Наскрізний проєкт з дисципліни «Інтелектуальні інформаційні системи».
Предметна область: **керування мікрокліматом теплиці** (томат; температура, вологість, CO₂, освітленість).

Паспорт проєкту: [docs/lab01_pasport.md](docs/lab01_pasport.md)


## Запуск
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python src/test_clips.py

## Структура
- `docs/` — звіти в текстовому вигляді
- `knowledge/` — словник, правила CLIPS, онтологія
- `data/raw`, `data/processed` — вихідні та підготовлені дані
- `src/` — код
- `reports/` — звіти .docx / .pdf
