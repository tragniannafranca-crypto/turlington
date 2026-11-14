from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "Atlante_Turlington_30.xlsx"
IMAGE_DIR = ROOT / "immagini"

st.set_page_config(
    page_title="Turlington",
    page_icon="🧥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f7f4f0; color: #252120; }
    [data-testid="stHeader"] { background: rgba(247,244,240,0.9); }
    .block-container { max-width: 1500px; padding-top: 2.2rem; }
    h1, h2, h3 { color: #272020; letter-spacing: -0.025em; }
    .intro { color: #756b67; font-size: 1.05rem; margin-top: -.4rem; }
    div.stButton > button { border-radius: 7px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, sheet_name="Atlante", dtype={"SKU": str})
    required = {
        "Modello", "SKU", "Costruzione", "Territorio", "Famiglia materiale",
        "Trattamento visivo", "Colore", "Prezzo (€)", "Chiave foto (SKU)",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError("Colonne mancanti nell'Excel: " + ", ".join(sorted(missing)))
    for column in [
        "Modello", "SKU", "Costruzione", "Territorio", "Famiglia materiale",
        "Trattamento visivo", "Colore", "Chiave foto (SKU)",
    ]:
        df[column] = df[column].fillna("").astype(str).str.strip()
    df["Prezzo (€)"] = pd.to_numeric(df["Prezzo (€)"], errors="coerce")
    return df


def euro(value):
    if pd.isna(value):
        return "Price unavailable"
    return "€" + f"{value:,.0f}".replace(",", ".")


CONSTRUCTION_LABELS = {
    "Monopetto": "Single-breasted",
    "Doppiopetto": "Double-breasted",
    "Non specificato": "Unspecified",
}
TERRITORY_LABELS = {
    "Material transformation": "Material variation",
}


def photo_for(row):
    key = row["Chiave foto (SKU)"] or row["SKU"]
    candidate = IMAGE_DIR / f"{key}.png"
    return candidate if candidate.is_file() else None


try:
    data = load_data()
except Exception as exc:
    st.error(f"Unable to read the Excel file: {exc}")
    st.stop()

territories = sorted(x for x in data["Territorio"].unique() if x)
territory_options = [TERRITORY_LABELS.get(x, x) for x in territories]
territory_lookup = {TERRITORY_LABELS.get(value, value): value for value in territories}
construction_values = sorted(x for x in data["Costruzione"].unique() if x)
construction_options = [CONSTRUCTION_LABELS.get(x, x) for x in construction_values]
construction_lookup = {
    CONSTRUCTION_LABELS.get(value, value): value for value in construction_values
}

st.title("Turlington")
st.markdown(
    '<div class="intro">Explore how the same jacket family changes through construction, materials, and visual details.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Filters")
    territory_filter = st.selectbox(
        "Aesthetic territory", ["All"] + territory_options, key="territory_filter_v2"
    )
    construction_filter = st.selectbox(
        "Construction", ["All"] + construction_options, key="construction_filter"
    )

filtered = data.copy()
if territory_filter != "All":
    source_territory = territory_lookup[territory_filter]
    filtered = filtered[filtered["Territorio"] == source_territory]
if construction_filter != "All":
    source_construction = construction_lookup[construction_filter]
    filtered = filtered[filtered["Costruzione"] == source_construction]

st.divider()
st.markdown(f"### Jacket gallery · {len(filtered)} styles")

selected_sku = st.session_state.get("selected_sku")
selected = data[data["SKU"] == selected_sku]
if not selected.empty:
    row = selected.iloc[0]
    st.markdown("#### Selected jacket")
    detail_left, detail_right = st.columns([1, 1])
    with detail_left:
        image_path = photo_for(row)
        if image_path:
            st.image(str(image_path), use_container_width=True)
        else:
            st.warning("Photo not found for SKU " + row["SKU"])
    with detail_right:
        st.subheader(row["Modello"].title())
        st.caption("SKU " + row["SKU"])
        st.metric("Price", euro(row["Prezzo (€)"]))
        detail_fields = [
            ("Aesthetic territory", "Territorio"),
            ("Construction", "Costruzione"),
            ("Material family", "Famiglia materiale"),
            ("Visual treatment", "Trattamento visivo"),
            ("Color", "Colore"),
        ]
        for label, field in detail_fields:
            value = row[field] or "Not specified"
            if field == "Costruzione":
                value = CONSTRUCTION_LABELS.get(value, value)
            elif field == "Territorio":
                value = TERRITORY_LABELS.get(value, value)
            st.markdown(f"**{label}:** {value}")
        if "Fonte ufficiale" in row and row["Fonte ufficiale"]:
            st.link_button("Open Dolce&Gabbana product page", row["Fonte ufficiale"])
    if st.button("Close details", key="close_detail"):
        del st.session_state["selected_sku"]
        st.rerun()

if filtered.empty:
    st.info("No jackets match these filters. Try changing your selections.")
else:
    products = filtered.to_dict(orient="records")
    for start in range(0, len(products), 3):
        cols = st.columns(3, gap="large")
        for col, product in zip(cols, products[start : start + 3]):
            with col:
                with st.container(border=True):
                    image_path = photo_for(product)
                    if image_path:
                        st.image(str(image_path), use_container_width=True)
                    else:
                        st.warning("Photo missing · " + product["SKU"])
                    st.markdown("**" + product["Modello"].title() + "**")
                    construction_label = CONSTRUCTION_LABELS.get(
                        product["Costruzione"], product["Costruzione"]
                    )
                    territory_label = TERRITORY_LABELS.get(
                        product["Territorio"], product["Territorio"]
                    )
                    st.caption(territory_label + " · " + construction_label)
                    st.write(product["Famiglia materiale"] + " · " + product["Trattamento visivo"])
                    st.markdown("**" + euro(product["Prezzo (€)"]) + "**")
                    if st.button("View details", key="details_" + product["SKU"]):
                        st.session_state["selected_sku"] = product["SKU"]
                        st.rerun()

st.caption("Classifications and prices are based on the sample spreadsheet.")
