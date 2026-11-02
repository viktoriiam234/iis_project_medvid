"""ЛР 5: прямий і зворотний ланцюг, траса, пояснення «ЯК» і «ЧОМУ».

Запуск із кореня репозиторію:
    python src/inference.py            # діалог зі зворотним ланцюгом (команди: чому, як)
    python src/inference.py forward    # прямий ланцюг по кроках на тестовому випадку
    python src/inference.py experiment # порівняльний експеримент (3 прогони)
"""
import sys
import clips


class PythonPrint(clips.Router):
    """Перехоплює вивід CLIPS (printout t ...) і друкує його через Python,
    щоб кирилиця коректно відображалася в консолі Windows."""
    def __init__(self):
        super().__init__("python-print", 50)

    def query(self, name):
        return name in ("stdout", "t")

    def write(self, name, message):
        sys.stdout.write(message)
        sys.stdout.flush()

RULES_CLP = "knowledge/rules.clp"

# ------------------------------------------------------------------
# База знань для зворотного ланцюга (ті самі правила, що в rules.clp)
# Умова:  "підціль"                      — доводиться іншими правилами
#         ("not", "підціль")             — підціль має бути хибною
#         (параметр, оператор, значення) — перевірка параметра, який питаємо
# ------------------------------------------------------------------
RULES = [
    ("R1", "провітрювання",
     [("температура", ">", 24), ("кватирки", "=", "закриті"), ("not", "дощ_або_вітер")],
     "якщо температура вище 24 °C, кватирки закриті і немає дощу чи сильного вітру — провітрити"),
    ("R6", "провітрювання",
     ["надмірна_вологість", ("not", "холодно_надворі")],
     "якщо вологість надмірна і надворі не холодно — провітрити"),
    ("R5", "провітрювання",
     [("час_доби", "=", "ніч"), ("температура", ">", 21)],
     "якщо вночі температура вище 21 °C — провітрити"),
    ("R2", "затінення",
     ["перегрів", ("кватирки", "=", "відкриті")],
     "якщо перегрів, хоча кватирки вже відкриті, — затінити"),
    ("R2a", "затінення",
     ["перегрів", "дощ_або_вітер"],
     "якщо перегрів, а провітрювати не можна через дощ чи вітер, — затінити"),
    ("R3", "затінення",
     [("сонячний_опік", "=", "так")],
     "якщо на плодах є сонячні опіки — затінити"),
    ("R7", "цикл_нагріву",
     ["надмірна_вологість", "холодно_надворі"],
     "якщо вологість надмірна, а надворі холодно, — цикл нагріву й провітрювання"),
    ("R8", "цикл_нагріву",
     ["надмірна_вологість", ("час_доби", "in", ("вечір", "світанок"))],
     "якщо вологість надмірна ввечері або на світанку — цикл нагріву й провітрювання"),
    ("R4", "обігрів",
     [("температура", "<", 15)],
     "якщо температура нижче 15 °C — увімкнути обігрів"),
    ("R10", "подача_co2",
     [("час_доби", "=", "день"), ("кватирки", "=", "закриті"), ("co2", "<", 800), ("not", "провітрювання")],
     "якщо вдень при закритих кватирках CO₂ нижче 800 ppm і провітрювати не треба — подавати CO₂"),
    ("R9", "зволоження",
     [("час_доби", "=", "день"), ("вологість", "<", 55)],
     "якщо вдень вологість нижче 55 % — зволожити повітря"),
    ("F11", "ризик_сірої_гнилі",
     [("вологість", ">=", 93)],
     "якщо вологість 93 % і вище — є ризик сірої гнилі"),
    ("E3", "ризик_сірої_гнилі",
     [("конденсат_на_листі", "=", "так"), ("ознаки_гнилі_за_фахівцем", "=", "так")],
     "якщо на листі конденсат і фахівець бачить ознаки гнилі — є ризик сірої гнилі"),
    # проміжні висновки
    ("N1", "перегрів", [("температура", ">", 29)], "температура вище 29 °C означає перегрів"),
    ("N2", "надмірна_вологість",
     [("вологість", ">", 85), ("год_вологість_понад_85", ">=", 1)],
     "вологість понад 85 % довше години означає надмірну вологість"),
    ("N3", "холодно_надворі", [("зовнішня_температура", "<", 10)],
     "надворі нижче 10 °C — холодно"),
    ("N4", "дощ_або_вітер", [("дощ_або_сильний_вітер", "=", "так")],
     "дощ або вітер понад 10 м/с забороняють відкривати кватирки"),
]

# Параметри, які можна запитати: (питання, вартість, тип)
# 1 — видно одразу, 2 — простий вимір / журнал, 3 — огляд рослин, 4 — фахівець
ASKABLE = {
    "температура": ("Яка температура повітря у відсіку, °C?", 1, float),
    "вологість": ("Яка відносна вологість у відсіку, %?", 1, float),
    "кватирки": ("Кватирки закриті, привідкриті чи відкриті?", 1, str),
    "час_доби": ("Яка зараз пора доби (ніч, світанок, день, вечір)?", 1, str),
    "зовнішня_температура": ("Яка температура надворі, °C?", 1, float),
    "дощ_або_сильний_вітер": ("Чи йде дощ або дме вітер понад 10 м/с? (так/ні)", 1, str),
    "год_вологість_понад_85": ("Скільки годин поспіль вологість трималася понад 85 % (журнал контролера)?", 2, float),
    "co2": ("Яка концентрація CO₂, ppm (портативний вимірювач)?", 2, float),
    "сонячний_опік": ("Чи є на плодах сонячні опіки (огляд рослин)? (так/ні)", 3, str),
    "конденсат_на_листі": ("Чи є на листі конденсат (огляд рослин)? (так/ні)", 3, str),
    "ознаки_гнилі_за_фахівцем": ("Чи підтверджує фітопатолог ознаки сірої гнилі? (так/ні)", 4, str),
}

HYPOTHESES = [
    ("H1", "провітрювання", "потрібне провітрювання"),
    ("H2", "затінення", "потрібне затінення"),
    ("H3", "цикл_нагріву", "потрібен цикл нагріву й провітрювання"),
    ("H4", "обігрів", "потрібен обігрів"),
    ("H5", "подача_co2", "потрібна подача CO₂"),
    ("H6", "зволоження", "потрібне зволоження"),
    ("H7", "ризик_сірої_гнилі", "є ризик сірої гнилі"),
]
NAMES = {g: t for _, g, t in HYPOTHESES} | {
    "перегрів": "перегрів", "надмірна_вологість": "надмірна вологість",
    "холодно_надворі": "надворі холодно", "дощ_або_вітер": "дощ або сильний вітер"}


def test(value, op, ref):
    return {">": lambda: value > ref, "<": lambda: value < ref, ">=": lambda: value >= ref,
            "=": lambda: value == ref, "in": lambda: value in ref}[op]()


class BackwardChainer:
    def __init__(self, rules, askable, ordered=True, user=None, verbose=True):
        self.rules, self.askable = rules, askable
        self.ordered = ordered          # упорядковувати запити за вартістю
        self.user = user                # dict для сценарного режиму; None — input()
        self.verbose = verbose
        self.values = {}                # параметр -> значення (не питаємо двічі)
        self.known = {}                 # підціль -> True/False (не доводимо двічі)
        self.proved_by = {}             # підціль -> правило, яким доведено
        self.stack = []                 # (гіпотеза/підціль, правило) — для «ЧОМУ»
        self.fired = 0                  # скільки правил спрацювало
        self.tried = 0                  # скільки правил перевірялося
        self.questions = []             # (параметр, вартість)
        self.why_requests = set()       # у сценарному режимі: при якому запиті сказати «чому»

    # ---------- вартість ----------
    def cost(self, cond, seen=()):
        """Оцінка вартості перевірки умови: сума вартостей ще не відомих параметрів."""
        if isinstance(cond, tuple) and cond[0] == "not":
            return self.cost(cond[1], seen)
        if isinstance(cond, tuple):
            return 0 if cond[0] in self.values else self.askable[cond[0]][1]
        if cond in self.known or cond in seen:
            return 0
        rules = [r for r in self.rules if r[1] == cond]
        return min((sum(self.cost(c, seen + (cond,)) for c in r[2]) for r in rules), default=99)

    def order(self, items, key):
        return sorted(items, key=key) if self.ordered else list(items)

    # ---------- запит ----------
    def say(self, *a):
        if self.verbose:
            print(*a)

    def ask(self, param):
        if param in self.values:
            return self.values[param]
        question, cost, typ = self.askable[param]
        while True:
            if self.user is not None:
                if param in self.why_requests:
                    self.say(f"  ? {question}\n  > чому")
                    self.explain_why(param)
                    self.why_requests.discard(param)
                answer = str(self.user[param])
                self.say(f"  ? {question}\n  > {answer}")
            else:
                answer = input(f"  ? {question}\n  > ").strip().lower()
                if answer == "чому":
                    self.explain_why(param)
                    continue
            try:
                value = typ(answer.replace(",", ".")) if typ is float else answer.strip().lower()
                break
            except ValueError:
                print("  Введіть число або «чому».")
        self.values[param] = value
        self.questions.append((param, cost))
        return value

    # ---------- доведення ----------
    # Результат: True (доведено), False (спростовано), None (відкладено: потрібен
    # запит, дорожчий за поточний ліміт). Кешуються лише остаточні результати.
    def check(self, cond, limit):
        if isinstance(cond, tuple) and cond[0] == "not":
            r = self.prove(cond[1], limit)
            return None if r is None else not r
        if isinstance(cond, tuple):
            param, op, ref = cond
            if param not in self.values and self.askable[param][1] > limit:
                return None                              # дорогий запит відкладаємо
            self.stack.append(("param", param))
            value = self.ask(param)
            self.stack.pop()
            return test(value, op, ref)
        return self.prove(cond, limit)

    def prove(self, goal, limit=4):
        if goal in self.known:                         # уже виведено — не доводимо вдруге
            return self.known[goal]
        rules = [r for r in self.rules if r[1] == goal]
        undecided = False
        for rule in self.order(rules, key=lambda r: sum(self.cost(c) for c in r[2])):
            rid, _, conds, text = rule
            self.tried += 1
            self.stack.append((goal, rule))
            result = True
            for c in self.order(conds, key=self.cost):  # дешевші умови першими
                r = self.check(c, limit)
                if r is False:                          # перша хибна умова зупиняє правило
                    result = False
                    break
                if r is None:
                    result = None
            self.stack.pop()
            if result:
                self.fired += 1
                self.known[goal] = True
                self.proved_by[goal] = rule
                return True
            undecided = undecided or result is None
        if undecided:
            return None
        self.known[goal] = False
        return False

    # ---------- пояснення ----------
    def explain_why(self, param):
        frames = [f for f in self.stack if f[0] != "param"]
        goal, (rid, _, _, text) = frames[-1]
        self.say(f"  Я запитую про «{param}», щоб перевірити правило {rid}: «{text}».")
        for g, (r, _, _, t) in reversed(frames[:-1]):
            self.say(f"  Висновок «{NAMES.get(goal, goal)}» потрібен для правила {r}: «{t}».")
            goal = g
        self.say(f"  Це потрібно для перевірки гіпотези «{NAMES.get(goal, goal)}».")

    def explain_how(self, goal, indent="  "):
        rid, _, conds, text = self.proved_by[goal]
        self.say(f"{indent}«{NAMES.get(goal, goal)}» — за правилом {rid}: «{text}», бо:")
        for c in conds:
            if isinstance(c, tuple) and c[0] == "not":
                self.say(f"{indent}  – не виконано «{NAMES.get(c[1], c[1])}» (спростовано раніше)")
            elif isinstance(c, tuple):
                p, op, ref = c
                ref_txt = " або ".join(ref) if op == "in" else ref
                v = self.values[p]
                v = int(v) if isinstance(v, float) and v.is_integer() else v
                self.say(f"{indent}  – {p} = {v} ({op} {ref_txt}), дано користувачем")
            else:
                self.explain_how(c, indent + "    ")

    # ---------- перебір гіпотез ----------
    def diagnose(self, hypotheses=HYPOTHESES):
        # з упорядкуванням: спершу всі гіпотези лише дешевими запитами (вартість <= 2),
        # дорогі (огляд рослин, фахівець) — тільки якщо дешевих даних не вистачило
        limits = (2, 4) if self.ordered else (4,)
        refuted = set()
        for limit in limits:
            if self.ordered:
                self.say(f"\n--- Прохід із запитами вартістю до {limit} ---")
            for hid, goal, title in hypotheses:
                if hid in refuted:
                    continue
                self.say(f"\n[{hid}] Перевіряю гіпотезу: {title}")
                r = self.prove(goal, limit)
                if r:
                    self.say(f"\nВИСНОВОК: {title} ({hid}).")
                    return hid, goal
                if r is False:
                    refuted.add(hid)
                    self.say(f"  Гіпотезу {hid} спростовано.")
                else:
                    self.say(f"  {hid}: потрібні дорожчі дані — перевірку відкладено.")
        self.say("\nВИСНОВОК: жодну гіпотезу не підтверджено — втручання не потрібне "
                 "або бракує знань для цієї ситуації.")
        return None, None


# ------------------------------------------------------------------
# Прямий ланцюг (CLIPS) по кроках
# ------------------------------------------------------------------
CASE_FACTS = [
    "(відсік (id А) (час_доби вечір) (температура 16) (вологість 90) (год_вологість_понад_85 2) "
    "(co2 500) (кватирки закриті))",
    "(погода (температура 5) (вологість 85) (вітер 3) (дощ ні))",
]
CASE_USER = {
    "температура": 16, "вологість": 90, "год_вологість_понад_85": 2, "co2": 500,
    "кватирки": "закриті", "час_доби": "вечір", "зовнішня_температура": 5,
    "дощ_або_сильний_вітер": "ні", "сонячний_опік": "ні", "конденсат_на_листі": "так",
    "ознаки_гнилі_за_фахівцем": "ні",
}


def forward(verbose=True):
    env = clips.Environment()
    env.add_router(PythonPrint())
    env.load(RULES_CLP)
    env.reset()
    for f in CASE_FACTS:
        env.assert_string(f)
    start = {f.index for f in env.facts()}
    trace = []
    while True:
        acts = list(env.activations())        # конфліктна множина (впорядкована)
        if not acts:
            break
        trace.append(acts[0].name)
        env.run(1)                            # рівно одне правило
    derived = [f for f in env.facts() if f.index not in start]
    if verbose:
        print("Спрацювало правил:", len(trace))
        for i, r in enumerate(trace, 1):
            print(f"{i:3d}. {r}")
        print(f"\nПороджено фактів: {len(derived)}")
        for f in derived:
            print("   ", f)
    return trace, derived


def experiment():
    trace, derived = forward(verbose=False)
    rows = [("Прямий ланцюг (усі факти дано)", len(trace), 0, 0, "цикл нагріву + циркуляція")]
    for ordered in (False, True):
        bc = BackwardChainer(RULES, ASKABLE, ordered=ordered, user=CASE_USER, verbose=False)
        hid, goal = bc.diagnose()
        rows.append((f"Зворотний ланцюг {'з упорядкуванням' if ordered else 'без упорядкування'}",
                     bc.fired, len(bc.questions), sum(c for _, c in bc.questions),
                     f"{hid}: {NAMES[goal]}"))
        print(f"\n{'з' if ordered else 'без'} упорядкування — запити: "
              + ", ".join(f"{p}({c})" for p, c in bc.questions)
              + f"; перевірено правил: {bc.tried}")
    print(f"\n{'Спосіб':38} {'Правил':>6} {'Запитів':>7} {'Вартість':>8}  Висновок")
    for r in rows:
        print(f"{r[0]:38} {r[1]:>6} {r[2]:>7} {r[3]:>8}  {r[4]}")


def dialog():
    print("Зворотний ланцюг. На будь-яке питання можна відповісти «чому».")
    bc = BackwardChainer(RULES, ASKABLE, ordered=True)
    hid, goal = bc.diagnose()
    while goal and input("\nВведіть «як», щоб побачити пояснення, або Enter для виходу: ").strip() == "як":
        bc.explain_how(goal)
        break


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dialog"
    {"forward": forward, "experiment": experiment, "dialog": dialog}[mode]()
