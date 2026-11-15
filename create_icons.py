from pathlib import Path


# Icon setup

ICON_DIR = Path("static/icons")
ICON_DIR.mkdir(parents=True, exist_ok=True)


# SVG helper

def make_svg(paths, color="#5B35F5"):
    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     width="32"
     height="32"
     viewBox="0 0 24 24"
     fill="none"
     stroke="{color}"
     stroke-width="1.9"
     stroke-linecap="round"
     stroke-linejoin="round">
    {paths}
</svg>
""".strip()


# Icons

icons = {
    "home": """
        <path d="M3 11.5 12 4l9 7.5"/>
        <path d="M5.5 10.5V21h13V10.5"/>
        <path d="M9.5 21v-6h5v6"/>
    """,

    "search": """
        <circle cx="11" cy="11" r="7"/>
        <path d="m20 20-4-4"/>
    """,

    "layers": """
        <path d="m12 2 9 5-9 5-9-5 9-5Z"/>
        <path d="m3 12 9 5 9-5"/>
        <path d="m3 17 9 5 9-5"/>
    """,

    "clock": """
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 7v6l4 2"/>
    """,

    "chart": """
        <path d="M5 20V10"/>
        <path d="M10 20V4"/>
        <path d="M15 20v-7"/>
        <path d="M20 20V7"/>
    """,

    "info": """
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 11v6"/>
        <path d="M12 7h.01"/>
    """,

    "file": """
        <path d="M6 2h8l4 4v16H6V2Z"/>
        <path d="M14 2v5h5"/>
        <path d="M9 12h6"/>
        <path d="M9 16h6"/>
    """,

    "target": """
        <circle cx="12" cy="12" r="8"/>
        <circle cx="12" cy="12" r="4"/>
        <path d="m12 12 7-7"/>
    """,

    "cpu": """
        <rect x="7" y="7" width="10" height="10" rx="1"/>
        <path d="M9 2v3M15 2v3M9 19v3M15 19v3"/>
        <path d="M2 9h3M2 15h3M19 9h3M19 15h3"/>
        <circle cx="12" cy="12" r="2"/>
    """,

    "bars": """
        <path d="M5 20v-5"/>
        <path d="M10 20V10"/>
        <path d="M15 20V5"/>
        <path d="M20 20V2"/>
    """,

    "monitor": """
        <rect x="3" y="4" width="18" height="13" rx="2"/>
        <path d="M8 21h8"/>
        <path d="M12 17v4"/>
    """,
}


# Save default purple icons

for name, paths in icons.items():
    svg = make_svg(paths)
    (ICON_DIR / f"{name}.svg").write_text(svg)


# Save extra color versions

(ICON_DIR / "home-white.svg").write_text(
    make_svg(icons["home"], "#FFFFFF")
)

(ICON_DIR / "search-white.svg").write_text(
    make_svg(icons["search"], "#E5ECF7")
)

(ICON_DIR / "layers-white.svg").write_text(
    make_svg(icons["layers"], "#E5ECF7")
)

(ICON_DIR / "clock-white.svg").write_text(
    make_svg(icons["clock"], "#E5ECF7")
)

(ICON_DIR / "chart-white.svg").write_text(
    make_svg(icons["chart"], "#E5ECF7")
)

(ICON_DIR / "info-white.svg").write_text(
    make_svg(icons["info"], "#E5ECF7")
)

(ICON_DIR / "cpu-blue.svg").write_text(
    make_svg(icons["cpu"], "#2878F5")
)

(ICON_DIR / "layers-purple.svg").write_text(
    make_svg(icons["layers"], "#643BFA")
)

(ICON_DIR / "bars-green.svg").write_text(
    make_svg(icons["bars"], "#12B98A")
)

(ICON_DIR / "file-purple.svg").write_text(
    make_svg(icons["file"], "#6238F6")
)

(ICON_DIR / "target-purple.svg").write_text(
    make_svg(icons["target"], "#6238F6")
)

print("Icons created.")