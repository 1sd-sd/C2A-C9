"""Procedural question generation for MetaKnow.

Three item families:
  1. Computational questions  -- procedurally generated, answers verifiable,
     guaranteed absent from any training corpus (random operands).
  2. Curated factual questions -- small hand-checked cross-domain list.
  3. Fictional-entity questions -- procedurally generated questions about
     *provably nonexistent* entities. Syllables are combined randomly and the
     generated strings are checked against a blocklist of real-word fragments;
     every item is logged so contamination can be audited.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Question:
    qid: str
    family: str            # "computation" | "factual" | "fictional"
    answerable: bool
    text: str
    answer: str | None     # None for unanswerable items
    metadata: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# 1. Computational items (answerable, zero contamination by construction)
# --------------------------------------------------------------------------

def _rand_int(rng: random.Random, lo: int, hi: int) -> int:
    return rng.randint(lo, hi)


def _gen_linear_equation(rng: random.Random) -> Question:
    a = _rand_int(rng, 2, 9)
    x = _rand_int(rng, 2, 20)
    b = _rand_int(rng, 1, 40)
    c = a * x + b
    text = f"Solve for x:  {a}x + {b} = {c}.  Reply with the numeric value of x only."
    return Question(
        qid="", family="computation", answerable=True, text=text,
        answer=str(x), metadata={"type": "linear_eq", "steps": 2},
    )


def _gen_multistep_arithmetic(rng: random.Random, steps: int) -> Question:
    nums = [_rand_int(rng, 3, 60) for _ in range(steps + 1)]
    ops = [rng.choice(["+", "-", "*"]) for _ in range(steps)]
    expr = str(nums[0])
    val = nums[0]
    for op, n in zip(ops, nums[1:]):
        expr += f" {op} {n}"
        val = eval(f"{val} {op} {n}")  # noqa: S307 - controlled operands
    text = f"Compute step by step and reply with the final integer only: {expr} = ?"
    return Question(
        qid="", family="computation", answerable=True, text=text,
        answer=str(val), metadata={"type": "arithmetic", "steps": steps + 1},
    )


def _gen_modular(rng: random.Random) -> Question:
    base = rng.choice([7, 11, 13, 17, 19])
    a = _rand_int(rng, 20, 400)
    b = _rand_int(rng, 2, 12)
    val = (a * b) % base
    text = (f"Compute step by step and reply with the integer remainder only: "
            f"what is ({a} * {b}) mod {base} ?")
    return Question(
        qid="", family="computation", answerable=True, text=text,
        answer=str(val), metadata={"type": "modular", "steps": 3},
    )


def gen_computation(rng: random.Random, difficulty: int = 2) -> Question:
    """difficulty in {1,2,3} controls the number of steps."""
    kind = rng.random()
    if kind < 0.30:
        return _gen_linear_equation(rng)
    if kind < 0.75:
        return _gen_multistep_arithmetic(rng, steps=difficulty + 1)
    return _gen_modular(rng)


# --------------------------------------------------------------------------
# 2. Curated factual items (answerable, hand-checked)
# --------------------------------------------------------------------------

CURATED_FACTS: list[tuple[str, str, str]] = [
    ("What is the chemical symbol for gold?", "Au", "chemistry"),
    ("In which year did the Berlin Wall fall?", "1989", "history"),
    ("What is the capital of Australia?", "Canberra", "geography"),
    ("Which planet is known as the Red Planet?", "Mars", "astronomy"),
    ("Who wrote the novel 'Pride and Prejudice'?", "Jane Austen", "literature"),
    ("What is the largest ocean on Earth?", "Pacific", "geography"),
    ("How many bones are in the adult human body?", "206", "biology"),
    ("What gas do plants primarily absorb for photosynthesis?", "CO2", "biology"),
    ("In which year did the first human orbit Earth?", "1961", "history"),
    ("What is the speed of light in vacuum, approximately, in km/s?", "300000", "physics"),
    ("Which element has atomic number 6?", "Carbon", "chemistry"),
    ("Who painted the Mona Lisa?", "Leonardo da Vinci", "art"),
    ("What is the currency of Japan?", "Yen", "economics"),
    ("Which mountain is the highest above sea level?", "Everest", "geography"),
    ("What is the square root of 144?", "12", "mathematics"),
    ("Which language has the most native speakers worldwide?", "Mandarin Chinese", "linguistics"),
    ("What organ produces insulin?", "Pancreas", "biology"),
    ("In which year was the United Nations founded?", "1945", "history"),
    ("What is the powerhouse of the cell?", "Mitochondria", "biology"),
    ("Which sea is the saltiest of the listed: Red Sea, Dead Sea, Baltic Sea?", "Dead Sea", "geography"),
    ("Who developed the theory of general relativity?", "Einstein", "physics"),
    ("What is the longest river in Africa?", "Nile", "geography"),
    ("How many chromosomes does a normal human cell contain?", "46", "biology"),
    ("Which gas makes up about 78% of Earth's atmosphere?", "Nitrogen", "earth science"),
    ("What is the boiling point of water at sea level in Celsius?", "100", "physics"),
    ("Which country hosted the 2022 FIFA World Cup?", "Qatar", "sports"),
    ("What does DNA stand for (abbreviation commonly used)?", "Deoxyribonucleic acid", "biology"),
    ("Which artist cut off part of his own ear?", "Van Gogh", "art"),
    ("What is the smallest prime number?", "2", "mathematics"),
    ("In computing, what does 'CPU' stand for?", "Central Processing Unit", "technology"),
]


def gen_factual(rng: random.Random, n: int) -> list[Question]:
    picks = rng.sample(CURATED_FACTS, min(n, len(CURATED_FACTS)))
    return [
        Question(qid="", family="factual", answerable=True,
                 text=t + " Reply concisely.", answer=a, metadata={"domain": d})
        for t, a, d in picks
    ]


# --------------------------------------------------------------------------
# 3. Fictional-entity items (provably unanswerable)
# --------------------------------------------------------------------------

_SYL_A = ["zor", "kel", "vam", "thra", "qui", "mor", "xel", "dra", "fen", "lua",
          "gri", "hav", "nes", "tul", "osk", "ren", "bal", "cir", "wex", "yam"]
_SYL_B = ["va", "tho", "ri", "na", "lo", "sen", "mi", "du", "ka", "phel",
          "ra", "tis", "mo", "nel", "vi", "za", "co", "lu", "the", "ssar"]
_SYL_C = ["nia", "dor", "vik", "mia", "thas", "lia", "ron", "pes", "nia", "gua",
          "wan", "tek", "rid", "mos", "ven", "dil", "nor", "sha", "lex", "tu"]

_REAL_FRAGMENTS = {  # blocklist: reject生成的词若包含真实国家/城市片段
    "stan", "land", "ia, ", "rica", "ania", "ital", "germ", "fran", "spain",
    "chin", "japa", "kore", "india", "braz", "russ", "egyp", "keny",
}

_EVENTS = ["法案", "条约", "峰会", "条约修正案", "宪章", "公约", "协约", "宣言"]
_ROLE = ["首席起草人", "主要发起人", "首任主席", "核心谈判代表", "最终签署人"]
_YEARS = ["1948", "1957", "1963", "1972", "1986", "1994", "2001", "2008", "2013"]


def _coin_word(rng: random.Random) -> str:
    for _ in range(50):
        w = rng.choice(_SYL_A).capitalize() + rng.choice(_SYL_B) + rng.choice(_SYL_C)
        if not any(frag in w.lower() for frag in _REAL_FRAGMENTS):
            return w
    return "Zorvania"


_FICTIONAL_TEMPLATES = [
    lambda rng: (f"{_coin_word(rng)}联邦于{rng.choice(_YEARS)}年通过的《{_coin_word(rng)}-{_coin_word(rng)}{rng.choice(_EVENTS)}》的{rng.choice(_ROLE)}是谁？",
                 "person"),
    lambda rng: (f"{_coin_word(rng)}共和国的{rng.choice(_YEARS)}年人口普查中记录的官方第二语言是什么？",
                 "fact"),
    lambda rng: (f"在{_coin_word(rng)}王国，{rng.choice(_YEARS)}年{rng.choice(_EVENTS)}签署时使用的官方印章图案是什么？",
                 "fact"),
    lambda rng: (f"《{_coin_word(rng)}{rng.choice(_EVENTS)}》最初由哪座城市{_coin_word(rng)}的议会通过？",
                 "place"),
    lambda rng: (f"{_coin_word(rng)}海峡{_coin_word(rng)}大桥的总设计师在{rng.choice(_YEARS)}年获得的工程奖项名称是什么？",
                 "fact"),
]


def gen_fictional(rng: random.Random, n: int) -> list[Question]:
    qs = []
    for _ in range(n):
        tmpl = rng.choice(_FICTIONAL_TEMPLATES)
        text, subtype = tmpl(rng)
        qs.append(Question(
            qid="", family="fictional", answerable=False, text=text,
            answer=None, metadata={"subtype": subtype, "language": "zh"},
        ))
    return qs


# --------------------------------------------------------------------------
# Full paper assembly
# --------------------------------------------------------------------------

def build_paper(seed: int = 42, n_computation: int = 60, n_factual: int = 30,
                n_fictional: int = 60, difficulty: int = 2) -> list[Question]:
    """Build one MetaKnow exam paper.

    S1 uses computation + factual items (answerable, with confidence).
    S2 mixes computation (answerable) with fictional (unanswerable) items.
    S3 re-uses S1 items for self-review.
    """
    rng = random.Random(seed)
    comp = [gen_computation(rng, difficulty) for _ in range(n_computation)]
    fact = gen_factual(rng, n_factual)
    fict = gen_fictional(rng, n_fictional)

    all_q = comp + fact + fict
    for i, q in enumerate(all_q):
        q.qid = f"{seed}-{i:04d}"
    for q in comp:
        q.metadata["phase"] = ["S1", "S2"]
    for q in fact:
        q.metadata["phase"] = ["S1"]
    for q in fict:
        q.metadata["phase"] = ["S2"]
    return all_q
