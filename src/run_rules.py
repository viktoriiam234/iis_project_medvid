"""ЛР 4: запуск продукційної бази знань і тестових сценаріїв.

Запуск із кореня репозиторію:
    python src/run_rules.py
"""
import sys
import clips


class PythonPrint(clips.Router):
    """Перехоплює вивід CLIPS (printout t ...) і друкує його через Python.
    Без цього в консолі Windows кирилиця з CLIPS перетворюється на «╨Р╤...»."""
    def __init__(self):
        super().__init__("python-print", 50)

    def query(self, name):
        return name in ("stdout", "t")

    def write(self, name, message):
        try:
            sys.stdout.write(message)
            sys.stdout.flush()
        except Exception as exc:        # діагностика: показати, що саме зламалося
            sys.__stderr__.write(f"[PythonPrint] {exc!r}\n")


RULES = "knowledge/rules.clp"

# Кожен сценарій — окремий набір початкових фактів:
# (опис, факти, очікувані дії, очікувані НЕ-дії, очікувана тривога)
SCENARIOS = {
    "T1": (
        "Перегрів удень, кватирки вже відкриті, надворі сухо",
        ["(відсік (id А) (час_доби день) (температура 31) (вологість 60) (co2 450) (кватирки відкриті))",
         "(погода (температура 24) (вологість 45))"],
        {"затінення", "випарне_охолодження"}, set(), False),
    "T2": (
        "Виняток V2: холодна волога ніч",
        ["(відсік (id А) (час_доби ніч) (температура 16) (вологість 90) (год_вологість_понад_85 2) (co2 500))",
         "(погода (температура 5) (вологість 85))"],
        {"цикл_нагріву_й_провітрювання", "циркуляція_повітря"}, {"провітрювання"}, False),
    "T3": (
        "Норма за всіма показниками",
        ["(відсік (id А) (час_доби день) (температура 23) (вологість 70) (co2 900))",
         "(погода (температура 18) (вологість 60))"],
        set(), set(), False),
    "T4": (
        "Винятки V1 і V4: спекотний вологий день, дефіцит CO2",
        ["(відсік (id А) (час_доби день) (температура 31) (вологість 75) (co2 600))",
         "(погода (температура 30) (вологість 80))"],
        {"провітрювання"}, {"випарне_охолодження", "подача_co2"}, False),
    "T5": (
        "Неповні дані: немає температури",
        ["(відсік (id А) (час_доби день) (вологість 60) (co2 900))",
         "(погода (температура 18) (вологість 60))"],
        set(), set(), False),
    "T6": (
        "Критичне переохолодження вночі",
        ["(відсік (id А) (час_доби ніч) (температура 8) (вологість 70) (co2 500))",
         "(погода (температура -2) (вологість 80))"],
        {"обігрів"}, set(), True),
    "T7": (
        "Перегрів у дощ: провітрювати не можна",
        ["(відсік (id А) (час_доби день) (температура 31) (вологість 60) (co2 900))",
         "(погода (температура 22) (вологість 65) (дощ так))"],
        {"затінення", "випарне_охолодження"}, {"провітрювання"}, False),
}


def run_scenario(env, facts):
    env.reset()                       # пороги з deffacts
    for f in facts:
        env.assert_string(f)
    env.run()
    recs = {str(f["дія"]): (str(f["режим"]), str(f["правило"]))
            for f in env.facts() if f.template.name == "рекомендація"}
    alarm = any(f.template.name == "тривога" for f in env.facts())
    states = sorted(str(f["назва"]) for f in env.facts() if f.template.name == "стан")
    return recs, alarm, states


def main():
    env = clips.Environment()
    env.add_router(PythonPrint())       # кирилиця з printout через Python
    env.load(RULES)
    rules = list(env.rules())
    print(f"Шаблонів: {len(list(env.templates()))}, правил: {len(rules)}\n")

    passed = 0
    for name, (desc, facts, want, not_want, want_alarm) in SCENARIOS.items():
        print(f"{name}. {desc}")
        recs, alarm, states = run_scenario(env, facts)
        ok = want <= set(recs) and not (not_want & set(recs)) and alarm == want_alarm
        if not want:                   # T3, T5: висновку бути не повинно
            ok = ok and not recs
        passed += ok
        print(f"  стани: {', '.join(states) or '—'}")
        print(f"  рекомендації: {', '.join(f'{d} ({m}, {r})' for d, (m, r) in recs.items()) or '—'}")
        print(f"  {'ЗБІГ' if ok else 'НЕ ЗБІГ'}\n")
    print(f"Пройдено {passed} з {len(SCENARIOS)} сценаріїв")


if __name__ == "__main__":
    main()
