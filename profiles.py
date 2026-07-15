"""Perfis rastreados (Instagram)."""

PROFILES = (
    {
        "username": "renansantosmbl",
        "display_name": "Renan Santos",
        "chart": True,
        "color": "#c0392b",
    },
    {
        "username": "flaviobolsonaro",
        "display_name": "Flávio Bolsonaro",
        "chart": True,
        "color": "#1a365d",
    },
    {
        "username": "lulaoficial",
        "display_name": "Lula",
        "chart": True,
        "color": "#d4a017",
    },
    {
        "username": "ronaldocaiado",
        "display_name": "Caiado",
        "chart": False,
        "color": "#16a34a",
    },
    {
        "username": "romeuzemaoficial",
        "display_name": "Zema",
        "chart": False,
        "color": "#7c3aed",
    },
)

CHART_USERNAMES = tuple(p["username"] for p in PROFILES if p["chart"])
USERNAME_TO_PROFILE = {p["username"]: p for p in PROFILES}
